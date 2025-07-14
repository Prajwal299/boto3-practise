
// pipeline{
//     agent :any
//     environment{
//       AWS_DEFAULT_REGION ="eu-north-1"
//     }
//   stages{
//     stage("git command"){
//   steps {
//                 git branch: 'main', url: 'https://github.com/Prajwal299/boto3-practise.git'
//             }
//     }
//     stage('Install Dependencies') {
//             steps {
//                bat "pip install boto3"
//             }
//         }
//     stage("launche ec2 with docker"){
//         steps{
//             withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'AWS-Creds']]){
//                 bat "ec2_creator.py"
//             } 
//         }
//     }
//   }
// }


pipeline {
    agent any

    environment {
        AWS_DEFAULT_REGION = "eu-north-1"
    }

    stages {

        stage('Clone GitHub Repo') {
            steps {
                git branch: 'main', credentialsId: 'your-git-credentials-id', url: 'https://github.com/Prajwal299/boto3-practise.git'
            }
        }

        stage('Install boto3') {
            steps {
                bat 'pip install boto3'
            }
        }

        stage('Launch EC2 with Docker') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'AWS-Creds']]) {
                    bat 'python3 ec2_creator.py'
                }
            }
        }

    }

    post {
        failure {
            echo 'Build failed!'
        }
        success {
            echo 'EC2 instance launched!'
        }
    }
}
