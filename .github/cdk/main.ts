import * as dedent from "dedent-js";
import { Construct } from "constructs";
import { App, CheckoutJob, Stack, Workflow } from "cdkactions";
import { DeployJob, DockerPublishJob } from "@pennlabs/kraken";

export class LASStack extends Stack {
  constructor(scope: Construct, name: string) {
    super(scope, name);
    const workflow = new Workflow(this, 'build-and-deploy', {
      name: 'Build and Deploy',
      on: 'push',
    });

    const checkJob = new CheckoutJob(workflow, 'check', {
      runsOn: 'ubuntu-latest',
      steps: [
        {
          name: 'Cache',
          uses: 'actions/cache@v2',
          with: {
            path: '~/.local/share/virtualenvs',
            key: "v0-${{ hashFiles('./Pipfile.lock') }}",
          },
        },
        {
          name: 'Install Dependencies',
          run: dedent`pip install pipenv
          pipenv install --deploy --dev`
        },
        {
          name: 'Lint (flake8)',
          run: 'pipenv run flake8 .',
        },
        {
          name: 'Run Tests',
          run: dedent`mkdir test-results
          pipenv run nose2 -c setup.cfg --with-coverage --plugin nose2.plugins.junitxml`
        }
      ],
      container: {
        image: `python:3.8`,
      },
      env: {
        DATABASE_URL: 'mysql://root:password@mysql:3306/mysql',
        REDIS_URL: 'redis://redis:6379',
      },
      services: {
        mysql: {
          image: 'mysql:latest',
          env: {
            MYSQL_ROOT_PASSWORD: 'password',
            MYSQL_DATABASE: 'mysql'
          },
          options: '--health-cmd="mysqladmin ping" --health-interval=10s --health-timeout=5s --health-retries=3 --entrypoint="docker-entrypoint.sh mysqld --default-authentication-plugin=mysql_native_password"'
        },
        redis: {
          image: 'redis:latest',
        },
      },
    });

    const publishJob = new DockerPublishJob(workflow, 'publish', {
      imageName: 'labs-api-server',
    },
      {
        needs: checkJob.id
      });

    new DeployJob(workflow, {}, {
      needs: publishJob.id
    });
  }
}

const app = new App();
new LASStack(app, 'labs-api-server');
app.synth();
