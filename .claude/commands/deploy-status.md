Check the GitHub Actions deployment workflow status for this repository.

Run `gh run list --repo seb-thomas/scaling-engine --limit 5` to see recent workflow runs.

If there's an in-progress deployment and you want to watch it until completion, use:
`gh run watch --repo seb-thomas/scaling-engine <run_id>`

If there's a failed deployment, check the logs with:
`gh run view <run_id> --repo seb-thomas/scaling-engine --log-failed`

For general details on any run:
`gh run view <run_id> --repo seb-thomas/scaling-engine`
