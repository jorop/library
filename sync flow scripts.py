import urllib


def handler(c):
    env_name = c.getEnvName()
    inputs = c.getInputs()
    # this flow is registered as webhook, triggered by a commit to the
    # repository. The commit sha is passed in .data_json.commit_sha
    # when started manually, it will sync from master
    try:
        commit_sha = inputs['data_json']['commit_sha']
    except Exception:
        commit_sha = 'master'
    # read the connection information of the private repository
    repo_info = c.setting('private git repo')
    # the git 'get' command ensures the content of the repository in a local
    # folder. it will clone or fetch and merge.
    c.task(
        'GIT',
        command='get',
        repository_url=repo_info['repository_url'],
        repository_path='repo',
        httpCookie=repo_info['httpCookie'],
        ref=commit_sha,
    ).run()
    # list all flows from the repository
    flows = c.list_dir('repo/flows', glob='**/*.py')
    c.setOutput('flows', flows)
    for flow in flows:
        content = c.file(f'repo/flows/{flow}')
        name = flow[:-3]
        urlname = urllib.parse.quote(name)
        flow_dict = {
            'name': name,
            'script': content,
        }
        # update the flow script in cloudomation. the API will automatically
        # fall back to POST (creating a record) when the record is not found.
        c.task(
            'REST',
            url=f'https://{env_name}.cloudomation.io/api/1/flow/{urlname}',
            method='PATCH',
            json=flow_dict,
            pass_user_token=True,
        ).runAsync()
    settings = c.list_dir('repo/settings', '**/*.yaml')
    c.setOutput('settings', settings)
    for setting in settings:
        content = c.file(f'repo/settings/{setting}')
        name = setting[:-5]
        urlname = urllib.parse.quote(name)
        setting_dict = {
            'name': name,
            'value': content,
        }
        # update the setting in cloudomation. the API will automatically
        # fall back to POST (creating a record) when the record is not found.
        c.task(
            'REST',
            url=f'https://{env_name}.cloudomation.io/api/1/setting/{urlname}',
            method='PATCH',
            json=setting_dict,
            pass_user_token=True,
        ).runAsync()
    c.success(message='all done')
