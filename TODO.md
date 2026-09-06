# Future plans
- Finish existing functionalities
    - Exploration tab in the App and filter-support from backend services
- Implement CI/CD functions
    - Prerequisites
        - Matrix builder helper function to determine which service is affected from changes
    - CI: Use GitHub Actions workflows
        - Backend: automatic Lint/Format/Test check
        - Android: automatic Build/Test/(Lint)/(Format) check
    - CD: Use (private) GHCR to store containers
        - After merging to main, upload the affected microservice containers
    - CD: Use k8s to run backend and ArgoCD to automatically pull and apply fresh container images
        - Use minikube via Docker
- Android functionalities
    - Offline-first
        - Import Room storage and change behavior to synchronize, but serve locally
    - Push-Notifications
        - Notify the users about fresh content from followed sources
- New AI-based microservice
    - Analyze posts from flagged sources and enrich the database with valuable fields
- Admin Web Client
    - To oversee the processes and contents in the platform and quickly take actions if necessary

# Schedule
- [ ] To Be Determined
