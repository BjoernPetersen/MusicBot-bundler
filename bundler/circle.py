import os

import requests

from bundler.error import NotFoundException


class Circle:
    _baseUrl = "https://circleci.com/api/v2"

    def __init__(self, token):
        self._token = token
        self._headers = {
            'Circle-Token': token
        }

    def get_pipelines(self, slug, branch):
        url = f"{self._baseUrl}/project/{slug}/pipeline?branch={branch}"
        response = requests.get(url, headers=self._headers)
        return response.json()['items']

    def get_workflows(self, pipeline_id):
        url = f"{self._baseUrl}/pipeline/{pipeline_id}/workflow"
        response = requests.get(url, headers=self._headers)
        return response.json()['items']

    def get_jobs(self, workflow_id):
        url = f"{self._baseUrl}/workflow/{workflow_id}/job"
        response = requests.get(url, headers=self._headers)
        return response.json()['items']

    def get_artifacts(self, slug, build_num):
        url = f"{self._baseUrl}/project/{slug}/{build_num}/artifacts"
        response = requests.get(url, headers=self._headers)
        return response.json()['items']


def create_slug(user, project) -> str:
    return f"github/{user}/{project}"


def find_jobs(client, workflow_id):
    return client.get_jobs(workflow_id)


def download(url, output):
    with open(output, 'wb') as f:
        response = requests.get(url)
        f.write(response.content)


def load_artifacts(client: Circle, slug, build_num, download_dir) -> str:
    arts = client.get_artifacts(slug, build_num)
    for artifact in arts:
        path = artifact['path']
        base_name = os.path.basename(path)
        print(f"Downloading {base_name}")
        filename = os.path.join(download_dir, base_name)
        download(artifact['url'], filename)
        return filename


def find_most_recent_workflow(client, slug, branch) -> str:
    for pipeline in client.get_pipelines(slug, branch):
        workflow = client.get_workflows(pipeline['id'])[0]
        if workflow['status'] == "success":
            print(f"Found successful pipeline: {pipeline['number']}")
            return workflow['id']
    raise NotFoundException("Could not find successful workflow")
