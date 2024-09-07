NAME = ./docker-compose.yml
LOCALIP = 'LOCALIP='

up: print_running set_localip run_ngrok
	@printf "Running configuration $(NAME) ..."
	@docker-compose -f $(NAME) up -d
	@echo "Your local IP-Address is:"
	@ifconfig | grep "inet 10." | awk '{print $$2}'
	@echo "The Domain is:"
	@echo $$(cat ./.env | grep "DOMAIN_NAME=" | cut -c14- | sed "s/^['\"]//;s/['\"]$$//")
	@printf "" >> send_to_subscribers.txt


print_running:
	@printf "Running configuration $(NAME) ..."

set_localip:
	@if ! grep -q "LOCALIP=" ./.env; then \
		echo "" >> .env; \
		printf "LOCALIP='" >> .env; \
		ifconfig | grep "inet 10." | awk '{printf $$2}' >> .env; \
		echo "'" >> .env; \
	fi	

run_ngrok:
	@if ! (docker ps -a | grep ngrok_container_pongping); then \
		docker run --name ngrok_container_pongping --net=host -it \
				-e NGROK_AUTHTOKEN=$$(cat ./.env | grep "NGROK_AUTHTOKEN=" | cut -c17- | sed "s/^['\"]//;s/['\"]$$//") \
				ngrok/ngrok:latest http \
				--domain=$$(cat ./.env | grep "DOMAIN_NAME=" | cut -c14- | sed "s/^['\"]//;s/['\"]$$//") 443 2>/dev/null \
				| printf "" ;\
	fi

ps:
	docker-compose -f $(NAME) ps

show:
	@echo "Your local IP-Address is:"
	@ifconfig | grep "inet 10." | awk '{print $$2}'
	@echo "The Domain is:"
	@echo $$(cat ./.env | grep "DOMAIN_NAME=" | cut -c14- | sed "s/^['\"]//;s/['\"]$$//")

logs:
	docker-compose -f $(NAME) logs

build:
	@printf "building configuration $(NAME) ... \n"
	@docker-compose -f $(NAME) up -d --build

down:
	@printf "Stopping configuration $(NAME) ... \n"
	@echo "Server Off\nOur server is now off until you are alive" > send_to_subscribers.txt
	@make send_email
	@docker-compose down

send_email:
	docker cp send_to_subscribers.txt my_django:/app/users/
	docker exec -it my_django chmod 777 /app/users/send_to_subscribers.txt
	docker exec -it my_django python manage.py send_email
	docker exec -it my_django rm -f /app/users/send_to_subscribers.txt

re:
	@printf "Rebuilding configuration $(NAME) ... \n"
	@echo "Server Off\nOur server is now off for a while" > send_to_subscribers.txt
	@make send_email
	@docker-compose -f $(NAME) down
	@printf "Running configuration $(NAME) ..."
	@make up
	@echo "SERVER ON!!\nOur Server is now back and ready for challengeing duales!!!!" > send_to_subscribers.txt

clean:
	@echo "Server Off Forever\nOur server is now off. We may be will be back.\n" > send_to_subscribers.txt; \
	make send_email; \
	docker stop $$(docker ps -qa);\
	docker rm $$(docker ps -qa);\
	docker rmi -f $$(docker images -qa);\
	docker network rm $$(docker network ls -q);\

clean1:
	@echo "Server Off Forever\nOur server is now off forever.\nThanks for your time with us!"; \
	make send_email;\
	docker-compose down -v;\
	docker stop $$(docker ps -qa);\
	docker rm $$(docker ps -qa);\
	docker rmi -f $$(docker images -qa);\
	docker network rm $$(docker network ls -q);\
	docker volume rm $$(docker volume ls -q);

re1:
	rm -rf */*/migrations; make clean1; make

clean_volumes:
	@docker volume rm $$(docker volume ls -q);


fclean:
	@printf "Complete clearning of all docker configuration ... \n"
	@docker stop $$(docker ps -qa);\
	docker system prune -a ;\
	docker system prune --all --force --volumes;\
	docker network prune --force;\
	docker volume rm  token-volume
