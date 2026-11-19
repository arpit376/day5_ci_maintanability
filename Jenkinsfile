// Jenkins pipeline for the LTE regression suite (module 5.3).
// Needs: an agent labelled 'lte-lab' with Python 3 and the Robot Framework Jenkins plugin.
// Not tested on a real Jenkins server in this kit: the stage commands are the same ones
// ./ci/local_pipeline.sh runs, and those are tested.
pipeline {
  agent { label 'lte-lab' }

  triggers { cron('H 1 * * *') }          // nightly build; commits come from the SCM webhook

  parameters {
    choice(name: 'MODE', choices: ['auto', 'commit', 'nightly', 'weekly'],
           description: 'auto = nightly when started by the timer, commit otherwise')
  }

  environment {
    // 'nightly' when the timer started the build, else 'commit'
    RUN_MODE = "${params.MODE != 'auto' ? params.MODE : (currentBuild.getBuildCauses('hudson.triggers.TimerTrigger$TimerTriggerCause') ? 'nightly' : 'commit')}"
  }

  stages {
    stage('Provision') {
      steps {
        sh 'python3 -m venv .venv && . .venv/bin/activate && pip install -q -r requirements.txt'
        sh '. .venv/bin/activate && python check_setup.py'
      }
    }
    stage('Smoke') {
      steps { sh ". .venv/bin/activate && robot -A lab.args --include smoke -d results/smoke --listener listeners/Notifier.py:results/notifications.log suites" }
    }
    stage('Full') {
      when { expression { env.RUN_MODE != 'commit' } }
      steps {
        sh ". .venv/bin/activate && pabot --processes 2 --testlevelsplit --pabotlib --resourcefile data/pool.dat -A lab.args --exclude long -d results/full suites"
      }
    }
  }

  post {
    always {
      // Publish and archive even when tests failed: a red build must keep its evidence.
      sh '''. .venv/bin/activate
            LAST=results/full; [ -f $LAST/output.xml ] || LAST=results/smoke
            mkdir -p results/report
            rebot -d results/report --output output.xml --xunit xunit.xml $LAST/output.xml || true'''
      robot outputPath: 'results/report', passThreshold: 100.0, unstableThreshold: 100.0
      archiveArtifacts artifacts: 'results/**', allowEmptyArchive: true
    }
    failure { echo 'Regression: see the Robot report and notifications.log' }
  }
}
