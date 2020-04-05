import json
import os
from typing import List
from zipfile import ZipFile

from bundler import circle, error, lambdas


def load_artifact(token: str, limited: bool, download_dir, artifact: dict) -> List[str]:
    user = artifact['user']
    project = artifact['project']
    if limited and not project.startswith('MusicBot'):
        raise error.ForbiddenException('Only MusicBot projects allowed')
    branch = artifact.get('branch') or 'master'
    requested_jobs = artifact['jobs']
    slug = circle.create_slug(user, project)

    client = circle.Circle(token)
    workflow_id = circle.find_most_recent_workflow(client, slug, branch)
    jobs = circle.find_jobs(client, workflow_id)

    files = []
    for job in jobs:
        if job['name'] in requested_jobs:
            filename = circle.load_artifacts(client, slug, job['job_number'], download_dir)
            files.append(filename)
    return files


def load_desktop_artifact(token: str, limited, base_dir, branch):
    artifact = {
        'branch': branch,
        'user': 'BjoernPetersen',
        'project': 'MusicBot-desktop',
        'jobs': ['build']
    }
    file = load_artifact(token, limited, base_dir, artifact)[0]
    target_dir = os.path.join(base_dir, 'musicbot-desktop')
    with ZipFile(file) as zipfile:
        name = zipfile.namelist()[0]
        zipfile.extractall(path=base_dir)
        extracted = os.path.join(base_dir, name)
        os.rename(extracted, target_dir)

    os.remove(file)
    return target_dir


def zip_files(base_dir, bot_dir) -> str:
    zip_path = os.path.join(base_dir, 'bundle.zip')
    with ZipFile(zip_path, mode='x') as zipfile:
        for folder, _, files in os.walk(bot_dir):
            for file in files:
                path = os.path.join(folder, file)
                arcname = path[len(base_dir):]
                zipfile.write(path, arcname=arcname)
    return zip_path


def handle_lambda(event, context):
    request_id = context.aws_request_id
    base_dir = f'/tmp/bundler-{request_id}'
    os.mkdir(base_dir)

    limited = False
    token = event['headers'].get('Circle-Token')
    if not token:
        limited = True
        token = os.environ["CIRCLE_TOKEN"]

    body = json.loads(event['body'])

    try:
        bot_dir = load_desktop_artifact(token, limited, base_dir, body.get('desktopVersion'))
        plugins_dir = os.path.join(bot_dir, 'plugins')
        os.mkdir(plugins_dir)

        for artifact in body['artifacts']:
            load_artifact(token, limited, plugins_dir, artifact)

        zipfile = zip_files(base_dir, bot_dir)
        object_id = lambdas.store_file(zipfile)
        url = lambdas.get_url(object_id)
    except error.StatusCodeException as e:
        return _create_error_response(e.code, e)
    except Exception as e:
        return _create_error_response(500, e)

    return {
        'statusCode': 200,
        'body': json.dumps({
            "url": url
        })
    }


def _create_error_response(code: int, e: Exception):
    return {
        'statusCode': code,
        'body': json.dumps({
            'errorMessage': str(e),
            'errorType': type(e).__name__
        })
    }
