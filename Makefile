NAME = ./docker-compose.yml

all:
	@printf "Running configuration $(NAME) ..."
	@mkdir -p ~/data/psql  
	@mkdir -p ~/data/vault 
	@mkdir -p ~/data/localip
	@ifconfig | grep "inet 10." | awk '{print $$2}'  > ~/data/localip/localip.txt
	@docker-compose -f $(NAME) up -d
	@echo "Your local IP-Address is:"
	@cat ~/data/localip/localip.txt
	@echo "The Domain is:"
	@echo $$(cat .domain_name.txt)

#@./ngrok_run.sh
ps:
	docker-compose -f $(NAME) ps

logs:
	docker-compose -f $(NAME) logs

build:
	@printf "building configuration $(NAME) ... \n"
	@docker-compose -f $(NAME) up -d --build

down:
	@printf "Stopping configuration $(NAME) ... \n"
	@docker-compose down

re:
	@printf "Rebuilding configuration $(NAME) ... \n"
	@docker-compose -f $(NAME) down
	@printf "Running configuration $(NAME) ..."
	@mkdir -p ~/data/psql  
	@mkdir -p ~/data/vault 
	@mkdir -p ~/data/localip
	@./ngrok_run.sh
	@ifconfig | grep "inet 10." | awk '{print $$2}'  > ~/data/localip/localip.txt
	@docker-compose -f $(NAME) up -d --build
	@echo "Your local IP-Address is:"
	@cat ~/data/localip/localip.txt
	@echo "The Domain is:"
	@echo $$(cat .domain_name.txt)

clean:
	@docker stop $$(docker ps -qa);\
	docker rm $$(docker ps -qa);\
	docker rmi -f $$(docker images -qa);\
	docker network rm $$(docker network ls -q);\
	rm ngrok_running

clean1:
	@docker-compose down -v;\
	docker stop $$(docker ps -qa);\
	docker rm $$(docker ps -qa);\
	docker rmi -f $$(docker images -qa);\
	docker network rm $$(docker network ls -q);\
	rm -rf ~/data/psql/*;\
	rm -rf ~/data/vault/*;\
	rm ngrok_running

re1:
	rm -rf */*/migrations; make clean1; make

clean_volumes:
	@docker volume rm $$(docker volume ls -q);

# clean: down
# 	@printf "Cleaninig  configuration $(NAME) ... \n"
# 	@docker stop $$(docker ps -qa)
# 	@docker system prune -a 

# fclean:
# 	@printf "Complete clearning of all docker configuration ... \n"
# 	@docker stop $$(docker ps -qa);\
# 	docker system prune -a ;\
# 	docker system prune --all --force --volumes;\
# 	docker network prune --force;\
# 	docker volume rm srcs_db-volume;\
# 	docker volume rm srcs_wp-volume;
