// Jenkinsfile

pipeline {
    agent any

    environment {
        AWS_DEFAULT_REGION = "eu-north-1"
    }

    stages {
        stage('Install Python Dependencies') {
            steps {
               bat "pip install boto3 paramiko"
            }
        }

        stage('Provision and Configure EC2 Instance') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'AWS-Creds']]) {
                    // THE DEFINITIVE FIX:
                    // 1. Change the Windows console to UTF-8 mode (chcp 65001)
                    // 2. Then run the python script.
                    // The '&&' ensures the code page is set first.
                    bat 'chcp 65001 && python ec2_creator.py'
                } 
            }
        }
    }

    post {
        success {
            echo 'Build successful! EC2 instance launched and configured.'
            archiveArtifacts artifacts: '*.pem', followSymlinks: false
        }
        failure {
            echo 'Build FAILED. Check the console output for errors.'
        }
    }
}