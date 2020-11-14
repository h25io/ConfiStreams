let canvasSize = 512;

let nbFrames = 180;

let squares = [];
let nbSquares = 8;
let squareSize = canvasSize/nbSquares;
let maxDelay = 100;
let nbOutside = 2;

function setup() {
  createCanvas(canvasSize, canvasSize);
  for(let x=-nbOutside; x<nbSquares+nbOutside; x++) {
    let row = [];
    for(let y=0-nbOutside; y<nbSquares+nbOutside; y++) {
      // let delay = random()*maxDelay;
      let delay = maxDelay * (x + y) / 14;
      row.push(new Square(x*squareSize,
                     y*squareSize,
                     squareSize,
                     256*((x+y+1)%2),
                     delay));
    }
    squares.push(row);
  }
}

function draw() {
  frameId = frameCount % nbFrames;
  translate(canvasSize/2, canvasSize/2)
  rotate(map(frameId, 0, nbFrames, 0, PI/2))
  translate(-canvasSize/2, -canvasSize/2)
  for(let x=-nbOutside; x<nbSquares+nbOutside; x++) {
    for(let y=0-nbOutside; y<nbSquares+nbOutside; y++) {
      let sq = squares[x+nbOutside][y+nbOutside];
      if((x+y+1)%2) {
        sq.sqcolor = map(frameId - sq.delay, 0, nbFrames-maxDelay, 255, 0);
      } else {
        sq.sqcolor = map(frameId - sq.delay, 0, nbFrames-maxDelay, 0, 255);
      }
    }
  }
  
  squares.flatMap(l => l).forEach(function(s) {
    s.render();
  });
}

function Square(x,y,l,sqcolor, delay) {
  this.x = x;
  this.y = y;
  this.l = l;
  this.sqcolor = sqcolor;
  this.delay = delay;
  
  this.render = function() {
    fill(this.sqcolor);
    stroke(this.sqcolor);
    strokeWeight(0.5);
    square(this.x, this.y, this.l)
  }
}