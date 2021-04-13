[![Build Status](https://travis-ci.com/KMK-Git/Website-Api.svg?branch=master)](https://travis-ci.com/KMK-Git/Website-Api)
<!-- PROJECT LOGO -->
<br />
<p align="center">

  <h3 align="center">Website-Api</h3>

  <p align="center">
    A Web API built using AWS serverless components for my personal website.
    <br />
  </p>
</p>

<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li><a href="#license">License</a></li>
    <li><a href="#acknowledgements">Acknowledgements</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## About The Project

![Architecture](../assets/Architecture.png?raw=true)

A serverless API deployed on AWS to send me an email when the contact form is filled, an API to add my friends' birthdays to an Amazon DynamoDB table and a scheduler to send them birthday wishes. It uses Amazon API Gateway to receieve API requests, AWS Lambda for processing requests, Amazon Cognito for authentication & authorization, Amazon Cloudwatch for scheduling and Amazon SES to send emails.

### Built With

- [Various AWS Services](https://aws.amazon.com/)
- [AWS SAM](https://aws.amazon.com/serverless/sam/)
- [Travis CI](https://travis-ci.com/)

<!-- LICENSE -->
## License

Distributed under the MIT License. See `License` for more information.

<!-- CONTACT -->
## Contact

Project Link: [https://github.com/KMK-Git/Website-Api](https://github.com/KMK-Git/Website-Api)

<!-- ACKNOWLEDGEMENTS -->
## Acknowledgements
* [Best-README-Template](https://github.com/othneildrew/Best-README-Template)
