# Микросервисное Demo — Счётчик нажатий

![CI](https://github.com/alexunderkot/microservice_app/actions/workflows/python.yaml/badge.svg)
![Docker](https://img.shields.io/badge/Docker-compose-2496ED?logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)
![Elasticsearch](https://img.shields.io/badge/ELK-8.13-005571?logo=elastic&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-latest-E6522C?logo=prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-latest-F46800?logo=grafana&logoColor=white)
![Jaeger](https://img.shields.io/badge/Jaeger-latest-66CFE3?logo=jaeger&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-minikube-326CE5?logo=kubernetes&logoColor=white)
![Helm](https://img.shields.io/badge/Helm-chart-0F1689?logo=helm&logoColor=white)
![Ansible](https://img.shields.io/badge/Ansible-playbook-EE0000?logo=ansible&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-docker-7B42BC?logo=terraform&logoColor=white)

Учебный проект для практики DevOps-инструментов. Простое микросервисное приложение — кнопка с инкрементом счётчика — с полным observability-стеком: метрики, логи и трейсинг.

---

## Архитектура

```
Пользователь
    │
    ▼
[web :5050]  ──────────►  [api :5000]
    │                          │
    │                       [Redis]
    │
    ├── метрики ──────►  [Prometheus :9090]  ──►  [Grafana :3000]
    │                         │
    │                    [Alertmanager :9093]
    │
    ├── логи ──────────►  [Filebeat]  ──►  [Logstash :5044]  ──►  [Elasticsearch :9200]  ──►  [Kibana :5601]
    │
    └── трейсы ────────►  [Jaeger :16686]
```

### Сервисы

| Сервис | Порт | Описание |
|---|---|---|
| web | 5050 | Flask-фронтенд, отображает счётчик и кнопку |
| api | 5000 | Flask-бэкенд, хранит и инкрементирует счётчик |
| Redis | 6379 | Хранение счётчика |
| Prometheus | 9090 | Сбор метрик с сервисов |
| Grafana | 3000 | Визуализация метрик |
| Alertmanager | 9093 | Алерты (срабатывает при ≥10 нажатиях) |
| Elasticsearch | 9200 | Хранение логов |
| Logstash | 5044 | Обработка и парсинг логов |
| Kibana | 5601 | Просмотр и поиск по логам |
| Filebeat | — | Сборщик логов из Docker-контейнеров |
| Jaeger | 16686 | Распределённый трейсинг |

---

## Быстрый старт

### Требования

- Docker Desktop
- Git

### Запуск

```bash
git clone https://github.com/alexunderkot/microservice_app.git
cd microservice_app
docker compose up -d --build
```

Подождать ~60 секунд пока поднимутся Elasticsearch и Kibana.

### Интерфейсы

| Сервис | URL | Логин |
|---|---|---|
| Приложение | http://localhost:5050 | — |
| Grafana | http://localhost:3000 | admin / admin |
| Kibana | http://localhost:5601 | — |
| Prometheus | http://localhost:9090 | — |
| Jaeger | http://localhost:16686 | — |
| Alertmanager | http://localhost:9093 | — |

---

## Метрики (Prometheus + Grafana)

Сервисы отдают метрики на эндпоинте `/metrics`:

- `app_clicks_total` — общее количество нажатий кнопки
- `api_requests_total{endpoint}` — количество запросов по эндпоинтам api
- `web_requests_total{endpoint}` — количество запросов по эндпоинтам web

**Алерт:** при достижении 10 нажатий Alertmanager отправляет предупреждение через Telegram-бота.

---

## Логи (ELK Stack)

Логи собираются автоматически из всех Docker-контейнеров через Filebeat.

Цепочка:
```
контейнер → Filebeat → Logstash → Elasticsearch → Kibana
```

Логи структурированы в JSON с полями `timestamp`, `level`, `service`, `message`.

### Поиск в Kibana

1. Открыть http://localhost:5601
2. Перейти в **Discover** → выбрать data view `app-logs-*`
3. Примеры KQL-запросов:

```
service: "api"
service: "web" and level: "ERROR"
message: "Counter incremented"
```

---

## Трейсинг (Jaeger)

Каждый запрос от пользователя отслеживается сквозь всю цепочку сервисов.

Пример трейса при нажатии кнопки:
```
web: POST /click
    └── web: POST http://api:5000/increment
            └── api: POST /increment
```

Открыть http://localhost:16686 → выбрать сервис **web** → **Find Traces**.

---

## Kubernetes + Helm

Приложение задеплоено в minikube через Helm chart.

### Запуск

```bash
minikube start --driver=docker
helm install myapp ./microservice-app
```

### Стек в кластере

| Ресурс | Тип | Реплики |
|---|---|---|
| api | Deployment | 2 |
| web | Deployment | 2 |
| jaeger | Deployment | 1 |
| redis | StatefulSet | 1 |

### Сервисы

| Сервис | Тип | Порт |
|---|---|---|
| myapp-api | ClusterIP | 5000 |
| myapp-web | NodePort | 30050 |
| myapp-jaeger | ClusterIP | 16686 |
| myapp-redis | ClusterIP | 6379 |

### Полезные команды

```bash
kubectl get pods
kubectl get services
kubectl logs <pod> --tail 20
helm list
helm upgrade myapp ./microservice-app
helm uninstall myapp
```

---

## Инфраструктура (infra/)

Папка `infra/` содержит код для автоматизации развёртывания.

### Terraform (infra/terraform/)

Поднимает стек приложения через Docker провайдер — контейнеры api, web, redis и сеть.

```bash
cd infra/terraform
terraform init
terraform apply
```

### Ansible (infra/ansible/)

Настраивает Linux-сервер с нуля и деплоит приложение. Роли:

| Роль | Что делает |
|---|---|
| users | Создаёт пользователей admin и deploy, отключает вход по паролю |
| docker | Устанавливает Docker CE, добавляет пользователей в группу docker |
| nginx | Устанавливает nginx, настраивает reverse proxy с HTTPS (self-signed) |
| deploy | Запускает контейнеры api, web, redis через Docker |
| firewall | Настраивает ufw: разрешает 22, 80, 443, блокирует остальное |

```bash
cd infra/ansible
ansible-playbook site.yml --limit vm
```

После выполнения приложение доступно по HTTPS на целевом сервере.

---

## Структура проекта

```
microservice_app/
├── api/                    # Flask API-сервис
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── web/                    # Flask веб-сервис
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── elk/                    # Конфиги ELK
│   ├── filebeat.yml
│   └── logstash/
│       └── logstash.conf
├── prometheus/             # Конфиги Prometheus
│   ├── prometheus.yml
│   └── rules/
│       └── alerts.yml
├── grafana/                # Provisioning Grafana
│   └── provisioning/
│       └── datasources/
│           └── datasource.yml
├── alertmanager/           # Конфиг Alertmanager
│   └── alertmanager.yml
├── microservice-app/       # Helm chart
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
├── infra/                  # Инфраструктурный код
│   ├── terraform/          # Docker провайдер
│   └── ansible/            # Роли для настройки сервера
├── .github/
│   └── workflows/          # CI
│       ├── docker.yaml
│       └── python.yaml
└── docker-compose.yaml
```

---

## Технологии

- **Python 3.11** + **Flask 3.0** — бэкенд и фронтенд
- **Redis** — хранение состояния счётчика
- **Docker Compose** — оркестрация контейнеров локально
- **Kubernetes (minikube)** + **Helm** — оркестрация в кластере
- **Prometheus + Grafana** — метрики и визуализация
- **ELK Stack 8.13** (Elasticsearch, Logstash, Kibana) + Filebeat — централизованное логирование
- **Jaeger** + **OpenTelemetry** — распределённый трейсинг
- **Alertmanager** — алертинг в Telegram
- **Terraform** — инфраструктура как код (Docker провайдер)
- **Ansible** — автоматизация настройки сервера (пользователи, Docker, nginx, деплой)
- **GitHub Actions** — CI/CD
