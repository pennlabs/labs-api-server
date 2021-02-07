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
      ],
      container: {
        image: `python:3.8`,
      },
      env: {
        REDIS_URL: 'redis://redis:6379',
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
