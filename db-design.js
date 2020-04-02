/*
+------------+
|            |
| Brand      |
|            |
+---+--------+
    |
    |        +------------+
    +--------+ Episode    +---------+---------+
    |        |            |         |         |
    |        +------------+     +---+--+   +--+---+
    |                           | Book |   | Book |
    |        +------------+     +------+   +------+
    +--------+ Episode    +-------------------+
    |        |            |         |         |
    |        +------------+     +---+--+   +--+---+
    |                           | Book |   | Book |
    |        +------------+     +------+   +------+
    +--------+ Episode    +-------------------+
             |            |         |         |
    +        +------------+     +---+--+   +--+---+
                                | Book |   | Book |
    +                           +------+   +------+
*/


// Brand
[{
    id: uuid,
    pid: String,
    title: String,
    synopsis: String,
    ownership: {
        key: String,
        title: String
    },
    type: brand
},{
    ...
}]

// Episode
[{
    id: uuid,
    pid: String,
    date: Date,
    title: String,
    short_synopsis: String,
    medium_synopsis: String,
    long_synopsis: String,
    image: String,
    parent: uuid,
    books: [{book: bookObject},{ ... }],
    ownership: {
        key: String,
        title: String
    },
    type: episode
},{
    ...
}]

// Book
[{
    id: uuid,
    title: String,
    image: String,
    author: String,
    link: String,
    parent: uuid,
    type: book
},{
    ...
}]