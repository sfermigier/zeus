from io import BytesIO

from zeus.artifacts.coverage import CoverageHandler
from zeus.models import FileCoverage


def test_cobertura_result_generation(default_job, sample_cobertura):
    fp = BytesIO(sample_cobertura.encode('utf-8'))

    handler = CoverageHandler(default_job)
    results = handler.get_coverage(fp)

    assert len(results) == 2

    r1 = results[0]
    assert type(r1) == FileCoverage
    assert r1.job_id == default_job.id
    assert r1.project_id == default_job.project_id
    assert r1.organization_id == default_job.organization_id
    assert r1.filename == 'setup.py'
    assert r1.data == 'NUNNNNNNNNNUCCNU'
    r2 = results[1]
    assert type(r2) == FileCoverage
    assert r2.job_id == default_job.id
    assert r2.project_id == default_job.project_id
    assert r2.organization_id == default_job.organization_id
    assert r2.data == 'CCCNNNU'


def test_jacoco_result_generation(default_job, sample_jacoco):
    fp = BytesIO(sample_jacoco.encode('utf-8'))

    handler = CoverageHandler(default_job)
    results = handler.get_coverage(fp)

    assert len(results) == 1

    r1 = results[0]
    assert type(r1) == FileCoverage
    assert r1.job_id == default_job.id
    assert r1.project_id == default_job.project_id
    assert r1.organization_id == default_job.organization_id
    assert r1.filename == 'src/main/java/com/dropbox/apx/onyx/api/resource/stats/StatsResource.java'
    assert r1.data == 'NNNNCCCCNNCCUU'


def test_process(mocker, default_job):
    get_coverage = mocker.patch.object(CoverageHandler, 'get_coverage')
    process_diff = mocker.patch.object(CoverageHandler, 'process_diff')

    handler = CoverageHandler(default_job)

    process_diff.return_value = {
        'setup.py': set([1, 2, 3, 4, 5]),
    }

    # now try with some duplicate coverage
    get_coverage.return_value = [
        FileCoverage(
            job_id=default_job.id,
            project_id=default_job.project_id,
            organization_id=default_job.organization_id,
            filename='setup.py',
            data='CUNNNNCCNNNUNNNUUUUUU',
            lines_covered=2,
            lines_uncovered=7,
            diff_lines_covered=2,
            diff_lines_uncovered=7,
        )
    ]

    fp = BytesIO()
    handler.process(fp)
    get_coverage.assert_called_once_with(fp)

    get_coverage.reset_mock()

    get_coverage.return_value = [
        FileCoverage(
            job_id=default_job.id,
            project_id=default_job.project_id,
            organization_id=default_job.organization_id,
            filename='setup.py',
            data='NUUNNNNNNNNUCCNU',
            lines_covered=2,
            lines_uncovered=4,
            diff_lines_covered=2,
            diff_lines_uncovered=4,
        )
    ]

    fp = BytesIO()
    handler.process(fp)
    get_coverage.assert_called_once_with(fp)

    file_cov = list(
        FileCoverage.query.unrestricted_unsafe().filter(
            FileCoverage.job_id == default_job.id,
        )
    )
    assert len(file_cov) == 1
    assert file_cov[0].filename == 'setup.py'
    assert file_cov[0].data == 'CUUNNNCCNNNUCCNUUUUUU'
    assert file_cov[0].lines_covered == 5
    assert file_cov[0].lines_uncovered == 9
    assert file_cov[0].diff_lines_covered == 1
    assert file_cov[0].diff_lines_uncovered == 2
