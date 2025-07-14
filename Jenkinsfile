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
                    // Force the Windows console into UTF-8 mode before running the Python script.
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