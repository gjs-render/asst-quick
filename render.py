<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Math Tutor</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
</head>
<body>
    <h1>Math Tutor</h1>
    <form id="solve-form">
        <label for="input">Enter your math question:</label>
        <input type="text" id="input" name="input" required>
        <button type="submit">Solve</button>
    </form>
    <div id="response"></div>
    <script>
        $(document).ready(function() {
            $('#solve-form').submit(function(event) {
                event.preventDefault(); // Prevent the form from submitting the traditional way
                const userInput = $('#input').val();
                // Send the input to the Flask backend
                $.ajax({
                    type: 'POST',
                    url: '/solve',
                    contentType: 'application/json',
                    data: JSON.stringify({ input: userInput }),
                    success: function(response) {
                        console.log('Response:', response); // Log the response
                        $('#response').text(response.response); // Display the response in the HTML
                    },
                    error: function(xhr) {
                        $('#response').text('Error: ' + xhr.responseJSON.error); // Display error message
                    }
                });
            });
        });
    </script>
</body>
</html>
