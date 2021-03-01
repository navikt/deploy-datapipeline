module.exports = (github, context, core) => {
    const lib = require(`${process.env.GITHUB_WORKSPACE}/.github/workflows/lib.js`)(github, context);
    const title = "Terraform Apply Results";

    function getRunId() {
        function extractRunId(comment) {
            const pattern = /Run ID: (?<run_id>\S+)/m
            const m = comment.body.match(pattern)
            if (m.groups.run_id !== undefined) {
                core.setOutput("run_id", m.groups.run_id)
                return Promise.resolve(m.groups.run_id)
            }
            let reason = `Failed to find Run ID in comment ${comment.id}`
            core.setFailed(reason)
            return Promise.reject(reason)
        }
        return lib.findComment("Terraform Plan Results")
            .then(extractRunId)
    }

    function addComment(outcomes) {
        function generateCommentBody() {
            const apply = decodeURIComponent(process.env.APPLY);
            const main = `
| | |
| --- | --- |
| Terraform Initialization ⚙️ | ${lib.resultIcon(outcomes.init)} |
| Terraform Apply 📖 | ${lib.resultIcon(outcomes.apply)} |
`;
            return lib.generateCommentBody(title, "Apply", main, apply);
        }

        return Promise
            .all([
                lib.findComment(title),
                generateCommentBody()
            ])
            .then(lib.updateComment);
    }

    function preApplyChecks() {
        function isMergeable() {
            return github.pulls.get({
                pull_number: context.issue.number,
                owner: context.repo.owner,
                repo: context.repo.repo
            })
                .then((pr) => {
                    return Promise.all([
                        Promise.resolve(pr.mergeable_state === "dirty"),
                        Promise.resolve(pr.mergeable_state === "behind"),
                    ]);
                })
        }

        function isApproved() {
            const options = github.pulls.listReviews.endpoint.merge({
                pull_number: context.issue.number,
                owner: context.repo.owner,
                repo: context.repo.repo,
            });

            console.log("Looking for reviews");
            let approved = false;
            return github.paginate(options)
                .then((reviews) => {
                    for (const review of reviews) {
                        if (review.state.toUpperCase() === "REQUEST_CHANGES") {
                            console.log("Found review requesting changes");
                            return Promise.resolve(false);
                        }
                        if (review.state.toUpperCase() === "APPROVED") {
                            console.log("Found approved reviews");
                            approved = true
                        }
                    }
                    return Promise.resolve(approved);
                })
        }

        return Promise.all([
            isMergeable(),
            isApproved()
        ])
            .then(([[dirty, behind], approved]) => {
                let applicable = true;
                if (dirty) {
                    core.warning("PR has conflicts!");
                    applicable = false;
                }
                if (behind) {
                    core.warning("PR is behind master!");
                    applicable = false;
                }
                if (!approved) {
                    core.warning("PR is not approved!");
                    applicable = false;
                }
                if (!applicable) {
                    core.setFailed("PR is not ready to be applied")
                }
                core.setOutput("applicable", applicable.toString());
            })
    }

    return {
        getRunId,
        addComment,
        preApplyChecks,
    };
};