function deleteNote(noteId) {
  fetch("/delete-note", {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({ noteId: noteId })
  })
  .then(response => response.json())  // Expecting a JSON response
  .then(data => {
      if (data.message === "Note deleted") {
          // Remove the note from the UI after successful deletion
          document.getElementById("note-" + noteId).remove();
      } else {
          alert('Failed to delete the note!');
      }
  })
  .catch(err => {
      console.error("Error deleting note:", err);
      alert('An error occurred while deleting the note.');
  });
}
