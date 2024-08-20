<?php
$conn = mysqli_connect("localhost", "username", "password", "database");

// Check connection
if (!$conn) {
    die("Connection failed: " . mysqli_connect_error());
}

// Simulate a vulnerable query
$id = $_GET['id'];
$query = "SELECT * FROM users WHERE id = '$id'";

$result = mysqli_query($conn, $query);

if (!$result) {
    echo "Error: " . mysqli_error($conn);
} else {
    while ($row = mysqli_fetch_assoc($result)) {
        echo "User: " . $row['username'] . "<br>";
    }
}

mysqli_close($conn);
?>