# Citizen Science and Computer Vision Analysis API

## Background and Implementation

Currently, there is a single analysis method using both Computer Vision (CV) and Citizen Science (CS). It is a "rule of thumb" concensus approach that is computationally lightweight and internally performed reasonably well in testing. Therefore, we decided to use it as the tool for the team to get to grips with the offerings of AWS (where MammalWeb is hosted), and develop the backend infrastructure to create a good foundation moving forward. For those unaware, a rule of thumb is a useful principle that is not always intended to be strictly accurate or reliable.

The rule part of the "rule of thumb" assesses at whether the first person to submit a classification agrees with CV predictions. The MammalWeb CS predictions are at a sequence level, whilst the CV predictions are at the object level. To make the CS and CV predictions comparable, the CV predictions across the sequence are aggregated, stripped of location information, and put into a set. The CS predictions are also placed into a set. The sequence is then labelled with all the predictions in the intersection of the CV and CS sets. If there is no agreement, the sequence is labelled as such which acts as a flag for further analysis. Where the CV does not predict anything, strictly speaking it means that the content of the sequence are unclassified. However, for our purpose here the sequence is classified as having nothing in it.

Is this the best and most rigorous approach? No. There is a reason it is called "rule of thumb". However, as previously mentioned, it works better than one would expect (at least for MammalWeb data and the CV used), and serves as a stepping stone to better things in the future.

MammalWeb is beginning to re-architect the backend to allow from more flexibility. It was agreed that this analysis tool would be a good fit to trial an API that can be spun up and down when needed. Due to some prior experience, the Python micro web framework "Flask" and the Web Server Gateway Interface (WSGI) server "Waitress" were chosen for implementation. The desire for the API to be spun up and down suited an approach that used containers, and so we decided to package the API in a Docker container. A docker container is compatible with AWS Fargate, a serverless compute product for containers that MammalWeb is trialing.

## Building the Image

The files in this repo are everything you need to create a container for the analysis API. You can do so pulling the repo, navigating to the directory and running:
```
docker build -t Foo:Bar .
```
where the -t indicates the tag the image will be given (i.e. replace the "Foo:Bar" with whatever you want). See the Docker website if more information is needed. To do so, git and the Docker CLI need to be installed.

## Running the Container

Currently, the internal port Waitress runs on is 8080 and the Flask route (the extension to the URL) is rule-of-thumb-v0. For example, if you wanted to run the image locally (with the internal port mapped externally to 8080) you could access the API at the URL http://127.0.0.1:8080/rule-of-thumb-v0.

When running the container, there are environment variables that need to be set. These are denoted below by being in all caps:

```
# This is the url for the MammalWeb API and is where the output of this Analysis API goes to get added to the MammalWeb database. 
MAMMALWEB_ENDPOINT="https://Foo.com/Bar" 

# This is a json string containing the details to obtain the authentication token from AWS cognito service for the MammalWeb API
AUTH_DETAILS= '{
    "cognitoEndPoint":"https://ADifferentFoo.com/Bar" ,
    "clientId":"asdfFooBar",
    "clientSecret":"SuperSecretString"
    }' 

#These are different IDs for different classes and scenarios. Internally, the AI_UNCLASSIFIED_ID is mapped to the NOTHING_ID
CS_AI_NO_AGREEMENT_ID="1" 
AI_UNCLASSIFIED_ID="2" 
NOTHING_ID="3"
```

## Pushing to the ECR

The Elastic Container Registry (ECR) is used to store the test and production images for MammalWeb. A guide follows for the next developer on how to push a local image. In the following instructions, replace all values in all caps locks with the relevant information.

To use the ECR, I have found that the best way is via the AWS CLI and the Docker CLI. To install, follow instructions on the AWS and Docker websites. Once you have configured AWS SSO, login using:

```
aws sso login --profile PROFILE_NAME
```

Once done, you need to authenticate the Docker CLI to the default registry so that you can push and pull images:
```
aws ecr get-login-password --profile PROFILE_NAME --region  REGION| docker login --username AWS --password-stdin AWS_ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com
```

After authentication, re-tag (if necessary) the local image:
```
docker tag LOCAL:TAG AWS_ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/REGISTRY_NAME
```

Each service has it's own registry, and there are two separate ones for testing and production:

- prod/ai-human-analysis/rule-of-thumb-v0
- test/ai-human-analysis/rule-of-thumb-v0

Choose the appropriate name. Once you have pushed the image you can specify when configuring AWS Fargate the desired image, and set all of the relevant environment variables.