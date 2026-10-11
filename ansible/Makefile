.PHONY: deps lint check deploy

deps:            ## установить коллекции Ansible
	ansible-galaxy collection install -r requirements.yml

lint:            ## статический анализ
	ansible-lint site.yml

check:           ## проверка синтаксиса (нужен group_vars/all/vault.yml, пусть даже незашифрованный пример)
	ansible-playbook site.yml --syntax-check

deploy:          ## развернуть на хостах из inventory (спросит пароль vault)
	ansible-playbook site.yml --ask-vault-pass
