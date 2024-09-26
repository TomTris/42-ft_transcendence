en.subject.pdf - original description of the Project.
# 🎮 **ft_transcendence**: Multiplayer Pong with AI, Blockchain, and DevOps

SCroll Down down down to have some images!

Welcome to **ft_transcendence**, an innovative take on the classic Pong game. This project includes multiplayer capabilities, AI-driven opponents, blockchain-based score storage, robust security, and docker for DevOps. It's designed to showcase a wide array of full-stack development skills and technologies.

## 📋 **Table of Contents**

- [Features](#features)
- [Technologies](#technologies)
- [Installation](#installation)
- [Gameplay Overview](#gameplay-overview)
- [Security & DevOps](#security--devops)
- [How to Play](#how-to-play)
- [Contact](#contact)

---

## 🌟 **Features**

- **Multiplayer Pong**: Challenge other players or an AI opponent to a 1v1 Pong match.
- **AI Opponent**: Play against an advanced AI that adapts and reacts in real time.
- **Blockchain Integration**: Tournament scores are securely stored using blockchain technology.
- **Authentication**: Secure user authentication using JWTs and Two-Factor Authentication (2FA).
- **Real-time Chat**: Chat with your opponents during gameplay.
- **Customizable Gameplay**: Choose from different game modes, power-ups, and maps.
- **3D Graphics**: Experience enhanced visuals built with Three.js and WebGL.
- **Cross-Platform**: Works seamlessly across different browsers.
- **Security**: Enhanced security using WAF (ModSecurity) and HashiCorp Vault for secrets management.
- **DevOps**: Dockerized environment.

---

## ⚙️ **Technologies**

- **Frontend**: HTML5, CSS3, JavaScript, Three.js/WebGL
- **Backend**: Django (Python Framework)
- **Database**: PostgreSQL
- **Blockchain**: Custom blockchain for score storage
- **Authentication**: JWT, 2FA (with email)
- **Security**: WAF (ModSecurity), HashiCorp Vault
- **DevOps**: Docker
- **Version Control**: Git
---


backend/: Contains Django app files, API logic, and blockchain code.
frontend/: Includes static files and templates for the 3D Pong game interface.
devops/: Configuration files for Docker.
🚀 Installation
Prerequisites
Docker and Docker Compose
Steps
Clone the repository:

bash
git clone https://github.com/TomTris/42-Ft_transcendence
cd ft_transcendence
fill out .env file.

Please change some character is Secret key, this is your django secret key.
Privatekey and deployer account is your metamask wallet and it needs to have holesky ETH in there.
You can collect it here: https://cloud.google.com/application/web3/faucet/ethereum/holesky

Additional for 2FA.
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
will be your own email. You need to enable SMTP for that.
I know it' complicate to enable it, so i commented out send_email() function  in ft_transcendence/users/utils and ft_transcendence/users/management/commands/send_email.py.
And for the code for 2FA, you can type docker logs my_django -f after you type make, i will print out the code when you register, login bla bla, so that you can ignore this step.

then, make
afterwards
https://localhost:443
If you are in 42 cluster, you can use your local IP address to connect remotely.
or, if you are the unique person, who at the moment run my project, you also can access it through: https://deciding-delicate-raptor.ngrok-free.app. It creates a tunnel linked to our server.
Then, Enjoy

🎮 Gameplay Overview
Play with friend Mode: You can play with your friend in same keyboard.

Remote Mode: Challenge real players in exciting 1v1 matches.
local Tournament and bonus online tournament!
AI Opponent: Face off against an intelligent AI that adapts to your strategies.
User management: Go to settings and change your data there.
Blockchain-Backed Scores: Tournament scores are stored on the blockchain for transparency and security.
🔐 Security & DevOps
WAF & ModSecurity: Protects against web vulnerabilities such as SQL Injection and XSS.
HashiCorp Vault: Securely manages secrets like API keys and credentials.
2FA & JWT: Provides secure, token-based authentication for users.
🕹️ How to Play
Sign Up or Log In using secure authentication (JWT and 2FA supported).
Join a match with either a real player or challenge the AI opponent.
Check scores on the blockchain for tournament rankings.
Chat in real-time with other players during your matches.
📞 Contact
If you have any questions or feedback, feel free to reach out:

Name: Tom.
Email: quoctrido.jb@gmail.com.
GitHub: https://github.com/TomTris.

Feel free to modify the sections as needed!

## Project Images
## Project Images

### Image 1
![Image 1](https://drive.google.com/uc?export=view&id=10GuKIm1XRqjMBcIf5REIF0ZWugwdJXuF)

### Image 3
![Image 3](https://drive.google.com/uc?export=view&id=1VYc0ZnA2Voz92lBalhOidGVObYmafJTY)

### Image 4
![Image 4](https://drive.google.com/uc?export=view&id=1pmLdsAmaN9QYEzHEfA_xWzMSIKk9_1Mb)

### Image 5
![Image 5](https://drive.google.com/uc?export=view&id=1rbcakLg7QR0m02XxROozrQJk1eK5IeWF)

### Image 6
![Image 6](https://drive.google.com/uc?export=view&id=1Z2ktDRcVfVj4vYuzBlmb4zWiT9LJOVVj)

### Image 6.5
![Image 6.5](https://drive.google.com/uc?export=view&id=1baCl1byk-7PemYoo7JRt9rAbqSsmYJcD)

### Image 7
![Image 7](https://drive.google.com/uc?export=view&id=18ioC2gEws_GgnruxiU2K3f4MQxjisMGU)

### Image 8
![Image 8](https://drive.google.com/uc?export=view&id=1G3912H-SDM6mpYvlzTSTAcOcbcvAL2nc)

### Image 9
![Image 9](https://drive.google.com/uc?export=view&id=1bZRn8L8OzEbx9HhWI6FySCITsASpz-tw)

### Image 10
![Image 10](https://drive.google.com/uc?export=view&id=1Jh34KmlNrlHqsgW_2j4xbSe1Pr3YoOY8)

### Image 11
![Image 11](https://drive.google.com/uc?export=view&id=176oNDPcQS5W5lVotIo7-Rx6-jlJkLGip)

### Image 12
![Image 12](https://drive.google.com/uc?export=view&id=1gKL1dAcScIX4SZWHHVkakjRKHtoOUmun)

### Image 13
![Image 13](https://drive.google.com/uc?export=view&id=1GMyjPRbqILW1BFjhTvNdb8CA1YdBajf9)

### Image 14
![Image 14](https://drive.google.com/uc?export=view&id=1yJrFxfHYOkihEzYtPscFTaD1G-2SCQ9g)

And afterall, i finished my Core Curriculum at 42heilbronn
### Image 2
![Image 2](https://drive.google.com/uc?export=view&id=1of8VNZia3aFbZla-dS8lLFG4QoYV6YgF)
