module.exports = (github, context) => {
    function updateComment([comment, comment_body]) {
        if (comment) {
            console.log(`Updating existing comment ${comment.id}`);
            github.issues.updateComment({
                comment_id: comment.id,
                owner: context.repo.owner,
                repo: context.repo.repo,
                body: comment_body
            });
        } else {
            console.log("Creating a new comment");
            github.issues.createComment({
                issue_number: context.issue.number,
                owner: context.repo.owner,
                repo: context.repo.repo,
                body: comment_body
            });
        }
    }

    function findComment(pattern) {
        const options = github.issues.listComments.endpoint.merge({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
        });

        console.log(`Looking for comment containing '${pattern}'`);
        return github.paginate(options)
            .then(comments => {
                for (const comment of comments) {
                    if (comment.body && comment.body.includes(pattern)) {
                        console.log(`Found existing matching comment: ${comment.id}`);
                        return comment;
                    }
                }
                console.log("No matching comment found");
                return null;
            });
    }

    function generateCommentBody(title, summary, main, output) {
        return `### ${title}

${main}

<details>
<summary>Show ${summary}</summary>

\`\`\`
${output}
\`\`\`

</details>

<details>
<summary>Additional details</summary>

Actor: @${context.actor}
Event: \`${context.eventName}\`
Action: \`${context.payload.action}\`
Workflow: \`${context.workflow}\`

</details>
`;
    }

    function resultIcon(outcome) {
        return outcome === "success" ? ":white_check_mark:" : ":no_entry_sign:";
    }

    function exposeJobResult(steps) {
        let result
        for (const key of Object.keys(steps)) {
            result = steps[key].outcome
            if (result !== "success") {
                console.log(`Job failed because of outcome of step ${key} was ${result}`)
                return result
            }
        }
        console.log(`Job result is ${result}`)
        return result
    }

    return {
        updateComment,
        findComment,
        generateCommentBody,
        resultIcon,
        exposeJobResult,
    };
};