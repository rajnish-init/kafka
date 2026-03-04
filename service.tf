module "users_sync_workers" {
  source   = "./modules/users_sync_workers"
  replicas = 2
  image    = "worker:v1"
}