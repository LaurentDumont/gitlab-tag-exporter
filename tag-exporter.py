from prometheus_client import start_http_server, Metric, REGISTRY
import os
import gitlab
import urllib3
import yaml
import time

urllib3.disable_warnings()

class GitlabCollector(object):
    def __init__(self):
        self._endpoint = '6666'

    def collect(self):
        GITLAB_PROJECTS_ID_LIST = os.getenv('GITLAB_PROJECTS_ID').split(',')
        GITLAB_API_TOKEN = os.getenv('GITLAB_API_TOKEN')
        GITLAB_API_URL = os.getenv('GITLAB_API_URL')

        gl = gitlab.Gitlab(GITLAB_API_URL, private_token=GITLAB_API_TOKEN, ssl_verify=False)


        for project_id in GITLAB_PROJECTS_ID_LIST:
            project = gl.projects.get(project_id)
            # Get the tag list for the project but with just one result (lower overhead)
            tags = project.tags.list(per_page='1')
            # Get most recent tag (and only one) - the tag list is returned 
            latest_tag = tags[0]


            gitlab_tag_metric = Metric('gitlab_tag_version',
        'Latest Gitlab tags for the project', 'summary')
            gitlab_tag_metric.add_sample('gitlab_tag_version',
        value='0', labels={'tag_version':str(latest_tag.name), 'project_name':str(project.name)})
            yield gitlab_tag_metric

            # Get the .gitlab-ci.yml from reach project in order to validate the target from the releases
            file_content = project.files.raw('.gitlab-ci.yml', 'master')
            test = yaml.safe_load(file_content)
            for library_name, version_value in test['variables'].items():
                if 'VERSION' in library_name:
                    library_version = version_value
                    project_version_req = Metric('project_version_req',
                    'Project versions requirements in Master branch', 'summary')
                    project_version_req.add_sample('project_version_req',
                    value='0', labels={'project':str(project.name), 'library_name':str(library_name),'target_version':str(library_version)})
                    yield project_version_req

if __name__ == '__main__':
  start_http_server(6666)
  REGISTRY.register(GitlabCollector())
  while True: 
    time.sleep(30)

