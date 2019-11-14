pipeline {

  options {
      timeout(time: 5, unit: 'MINUTES')
  }

  environment {
    GRACYQL_DOCKER =  'kairntech/gracyql'
  }

  agent {
    node {
      label 'master'
      customWorkspace "/home/karcherg/jenkins/${env.JOB_NAME}"
    }
  }

  stages {
    stage('Build Gracyql docker image') {
      steps {
        println "Building Gracyql docker image: ${GRACYQL_DOCKER}:${env.BRANCH_NAME}"
        script {
          sh "docker build -t ${GRACYQL_DOCKER}:${env.BRANCH_NAME} ."
        }
      }
    }
  }

  post {
    // trigger every-works
    always {
      echo "sending Systematic Build notification"
      emailext(body: '${DEFAULT_CONTENT}', mimeType: 'text/html',
        replyTo: '${DEFAULT_REPLYTO}', subject: '${DEFAULT_SUBJECT}',
        to: '${DEFAULT_RECIPIENTS}')
    }
  }

}
