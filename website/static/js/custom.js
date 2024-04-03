document.addEventListener("DOMContentLoaded", function() {
    var codeMirrorEditor = CodeMirror.fromTextArea(document.getElementById("codeEditor"), {
        mode: "python",
        lineNumbers: true,
        theme: "default",
        viewportMargin: Infinity
    });

    codeMirrorEditor.setOption("extraKeys", {
        "Cmd-Enter": function(cm) {
            submitCode(); // Function to submit the code
        },
        "Ctrl-Enter": function(cm) {
            submitCode(); // Function to submit the code
        }
    });

    function submitCode() {
        var code = codeMirrorEditor.getValue(); // Get code from CodeMirror editor
        var filename = $('input[name="filename"]').val(); // Get filename from the input field

        $.ajax({
            url: "/run_code",
            type: "POST",
            data: {
                code: code,
                filename: filename // Include filename in the AJAX request data
            },
            success: function(response) {
                $("#result").text(response.result);
            }
        });
    }

    $("#runCode").click(function() {
        submitCode();
    });

    $("#saveCode").click(function() {
        var code = codeMirrorEditor.getValue(); // Get code from CodeMirror editor
        var filename = $('input[name="filename"]').val(); // Get filename from the input field

        $.ajax({
            url: "/save_code",
            type: "POST",
            data: {
                code: code,
                filename: filename // Include filename in the AJAX request data
            },
            success: function(response) {
                $("#result").text(response.message); // Show success message
            },
            error: function(xhr, status, error) {
                $("#result").text("Error saving code: " + xhr.responseText); // Show error message
            }
        });
    });

    document.querySelectorAll('.filename-item').forEach(item => {
        item.addEventListener('click', function() {
            var filename = this.getAttribute('data-filename');
            fetch(`/get_code_by_filename?filename=${encodeURIComponent(filename)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.code !== undefined) {
                        codeMirrorEditor.setValue(data.code);
                        $('input[name="filename"]').val(data.filename);
                        $("#result").text(data.result || "No results."); // Update results display
                    } else {
                        $("#result").text(data.error || "Error loading snippet.");
                    }
                });
        });
    });

    // Load the first snippet automatically
    fetch(`/get_first_snippet`)
        .then(response => response.json())
        .then(data => {
            if (data.code) {
                codeMirrorEditor.setValue(data.code);
                $('input[name="filename"]').val(data.filename);
                $("#result").text(data.result || ""); // Also display the first result
            }
        });
});
