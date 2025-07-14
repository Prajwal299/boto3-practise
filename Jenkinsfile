
pipelines :[
    agent :any
    environment{
      AWS_DEFAULT_REGION ="eu-north-1"

    }
  stages{
    stage("git command"){
  steps {
                git branch: 'main', credentialsId: 'https://github.com/Prajwal299/boto3-practise.git'
            }
    }
    stage('Install Dependencies') {
            steps {
               bat "pip install boto3"
            }
        }
    stage("launche ec2 with docker"){
        steps{
            withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'AWS-Creds']]){
                bat "ec2_creator.py"
            } 
        }
    }
  }
]