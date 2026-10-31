# Local Kubernetes

Requires Docker Desktop running, Minikube, kubectl, Python 3 and Make.
Run from `deploy/`. Use `PYTHON=python3` with Make if needed.

## Start

```sh
minikube start -p briefly --driver=docker --container-runtime=containerd --kubernetes-version=v1.36.5 --cni=calico --cpus=4 --memory=5120
```

## First deployment

Copy `.env.example` to `.env` and fill in your credentials. Keep `.env` out of Git.
Ensure `argocd/application.yaml` tracks your published manifest branch (default: `master`)
and `argocd/image-updater.yaml` tracks that branch's published image tag.

```sh
kubectl --context briefly apply -f namespace.yaml
make secrets-check
make secrets
kubectl --context briefly apply --server-side --field-manager=briefly-bootstrap -k argocd/install
kubectl --context briefly wait --for=condition=Established crd/applications.argoproj.io crd/appprojects.argoproj.io crd/imageupdaters.argocd-image-updater.argoproj.io --timeout=120s
kubectl --context briefly -n argocd wait --for=condition=Ready pods --all --timeout=300s
kubectl --context briefly apply -f argocd/project.yaml
kubectl --context briefly apply -f argocd/application.yaml
kubectl --context briefly apply -f argocd/image-updater.yaml
make status
```

Stop if a command fails. Argo CD deploys the application from Git; the initial model download can take several minutes.

## Open Argo CD

```sh
kubectl --context briefly -n argocd port-forward service/argocd-server 18080:443
```

In another terminal, print the initial password:

```sh
python -c "import subprocess,base64; print(base64.b64decode(subprocess.check_output(['kubectl','--context','briefly','-n','argocd','get','secret','argocd-initial-admin-secret','-o','jsonpath={.data.password}'])).decode())"
```

Open https://localhost:18080, accept the local certificate and log in as `admin`.
Use your current password if you already changed it.

## Open the API

```sh
kubectl --context briefly -n briefly port-forward service/public-api 8000:8000
```

Open http://localhost:8000/docs. Keep port-forward terminals open; stop them with Ctrl+C.

## Stop

```sh
minikube stop -p briefly
```

Start again with `minikube start -p briefly`, then reopen the port-forwards. Stopping retains local data.
