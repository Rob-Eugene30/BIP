function deleteComment(commentId) {
    fetch("/delete-comment", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ commentId: commentId })
    })
    .then(response => response.json().catch(() => ({}))) // Prevents JSON parsing errors
    .then(data => {
        if (data.message === "Comment deleted") {
            // Remove the comment from the UI
            const commentElement = document.getElementById("comment-" + commentId);
            if (commentElement) {
                commentElement.remove();
            } else {
                console.warn("Comment element not found in DOM.");
            }
        } else {
            alert("Failed to delete the comment!");
        }
    })
    .catch(err => {
        console.error("Error deleting comment:", err);
        alert("An error occurred while deleting the comment.");
    });
}
