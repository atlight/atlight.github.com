#!/bin/bash

# add TOC
markdown-toc -i "$1.md"

# convert Markdown to HTML
github-markdown -s '/bootstrap/css/bootstrap.min.css' -t 'Demystifying DXF: LEADER and MULTILEADER (MLEADER) implementation notes' "$1.md" > "$1.html"

# remove unnecessary prefix from anchor IDs
sed -i 's/"user-content-/"/' "$1.html"

# get rid of GitHub's rel="nofollow"
sed -i 's/ rel="nofollow"//' "$1.html"

# add div container around the body
sed -i 's/^<body>$/<body><div class="container">/' "$1.html"
sed -i 's|^</body>$|</div></body>|' "$1.html"

# add additional custom stylesheet for this folder
sed -i 's|^</head>$|  <link rel="stylesheet" href="style.css">\n</head>|' "$1.html"
