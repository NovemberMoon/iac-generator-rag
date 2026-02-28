# Спецификация Terraform для Yandex Cloud

## 1. Базовая настройка провайдера (Provider)

Для работы с Yandex Cloud необходимо объявить провайдера yandex.

Требуемые параметры: token, cloud_id, folder_id, zone.

```
terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
}

provider "yandex" {
  zone = "ru-central1-a"
}

```

## 2. Создание виртуальной сети (VPC)

Любая инфраструктура начинается с сети (yandex_vpc_network) и подсети (yandex_vpc_subnet).

Обязательные параметры подсети: v4_cidr_blocks, zone, network_id.

```
resource "yandex_vpc_network" "main-network" {
  name = "production-network"
}

resource "yandex_vpc_subnet" "main-subnet" {
  name           = "production-subnet"
  zone           = "ru-central1-a"
  network_id     = yandex_vpc_network.main-network.id
  v4_cidr_blocks = ["10.0.0.0/24"]
}

```

## 3. Виртуальная машина (Compute Instance)

Для создания ВМ используется ресурс yandex_compute_instance.

Обязательные блоки:

- resources (cores, memory)
- boot_disk (image_id)
- network_interface (subnet_id, nat = true для доступа в интернет)

Пример создания веб-сервера на Ubuntu:

```
resource "yandex_compute_instance" "web-server" {
  name        = "nginx-web-server"
  platform_id = "standard-v1"

  resources {
    cores  = 2
    memory = 4
  }

  boot_disk {
    initialize_params {
      image_id = "fd87va5cc00gaq2f5qfb"
      size     = 20
    }
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.main-subnet.id
    nat       = true
  }

  metadata = {
    ssh-keys = "ubuntu:ssh-ed25519 AAAAC3NzaC1lZDI1..."
  }
}

```
