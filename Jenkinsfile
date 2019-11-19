pipeline {

  options {
      timeout(time: 5, unit: 'MINUTES')
  }

  environment {
    DOCKER_GRACYQL =  'kairntech/gracyql'
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
        println "building Gracyql docker image: ${DOCKER_GRACYQL}:all-${env.BRANCH_NAME}"
        script {
          sh "docker build -t ${DOCKER_GRACYQL}:all-${env.BRANCH_NAME} ."
        }
      }
    }
  }

  post {
    // trigger every-works
    always {
      println "sending Systematic Build notification"
      emailext(body: '${DEFAULT_CONTENT}', mimeType: 'text/html',
        replyTo: '${DEFAULT_REPLYTO}', subject: '${DEFAULT_SUBJECT}',
        to: '${DEFAULT_RECIPIENTS}')
    }
  }

}
