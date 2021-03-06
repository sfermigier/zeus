from flask import request

from zeus.models import Build, Job
from zeus.api import client

from .base import BaseHook


class JobHook(BaseHook):
    def post(self, hook, build_xid, job_xid):
        build = Build.query.filter(
            Build.organization_id == hook.organization_id,
            Build.project_id == hook.project_id,
            Build.provider == hook.provider,
            Build.external_id == build_xid,
        ).first()
        if not build:
            return self.respond('', 404)

        job = Job.query.filter(
            Job.provider == hook.provider,
            Job.external_id == job_xid,
            Job.build_id == build.id,
        ).first()

        json = request.get_json() or {}
        json['external_id'] = job_xid
        json['provider'] = hook.provider

        if job:
            response = client.put(
                '/projects/{}/{}/builds/{}/jobs/{}'.format(
                    hook.organization.name,
                    hook.project.name,
                    job.build.number,
                    job.number,
                ),
                json=json
            )
        else:
            response = client.post(
                '/projects/{}/{}/builds/{}/jobs'.format(
                    hook.organization.name,
                    hook.project.name,
                    build.number,
                ),
                json=json
            )

        return response
