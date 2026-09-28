#!/bin/bash
# 根据 Compose 镜像标签调整应用版本目录。

app_name=$1
old_version=$2

# 查找当前应用版本的 Compose 文件。
docker_compose_files=$(find apps/$app_name/$old_version -name docker-compose.yml)

for docker_compose_file in $docker_compose_files
do
	# 使用第一个服务的镜像标签作为应用版本。
	first_service=$(yq '.services | keys | .[0]' $docker_compose_file)

	image=$(yq .services.$first_service.image $docker_compose_file)

	# 仅处理带版本标签的镜像。
	if [[ "$image" == *":"* ]]; then
	  version=$(cut -d ":" -f2- <<< "$image")

	  # 去掉版本前面的 v。
	  trimmed_version=${version/#"v"}

      mv apps/$app_name/$old_version apps/$app_name/$trimmed_version
    fi
done
