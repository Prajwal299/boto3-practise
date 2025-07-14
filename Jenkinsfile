// // Jenkinsfile

// pipeline {
//     // Run on any available agent. Make sure Python3 and pip are installed on the agent.
//     agent any

//     environment {
//         // Set AWS region for the Boto3 script
//         AWS_DEFAULT_REGION = "eu-north-1"
//     }

//     stages {
//         // The 'checkout scm' step is automatically done by Jenkins at the start.
//         // No need for an extra 'git clone' stage.

//         stage('Install Python Dependencies') {
//             steps {
//                // Use 'bat' for Windows agents
//                // Ensure boto3 is installed. This command is safe to run even if it's already installed.
//                bat "pip install boto3"
//             }
//         }

//         stage('Launch EC2 Instance via Boto3') {
//             steps {
//                 // Use 'withCredentials' to securely inject your AWS credentials
//                 // The credential ID 'AWS-Creds' must exist in your Jenkins credentials store.
//                 withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'AWS-Creds']]) {
                    
//                     // FIX 2: On Windows, the command is 'python', not 'python3'.
//                     // This was the main cause of your build failure.
//                     bat 'python ec2_creator.py'
//                 } 
//             }
//         }
//     }

//     post {
//         // This block runs after all stages complete
//         success {
//             echo 'Build successful! EC2 instance launched and Flask app is deploying.'
//         }
//         failure {
//             echo 'Build FAILED. Check the console output for errors.'
//         }
//     }
// }




// Jenkinsfile

pipeline {
    agent any

    environment {
        AWS_DEFAULT_REGION = "eu-north-1"
    }

    stages {
        stage('Install Python Dependencies') {
            steps {
               // Install both boto3 and the new paramiko library for SSH
               bat "pip install boto3 paramiko"
            }
        }

        stage('Provision and Configure EC2 Instance') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'AWS-Creds']]) {
                    // Run the new script that handles both provisioning and SSH configuration
                    bat 'python ec2_creator.py'
                } 
            }
        }
    }

    post {
        success {
            echo 'Build successful! EC2 instance launched and configured via SSH.'
            // Archive the .pem file so you can download it from the Jenkins build page
            archiveArtifacts artifacts: '*.pem', followSymlinks: false
        }
        failure {
            echo 'Build FAILED. Check the console output for the exact error.'
        }
    }
}