let canvasSize = 512;

let nbFrames = 180;

let squares = [];
let nbSquares = 8;
let squareSize = canvasSize/nbSquares;

let maxDelay = nbFrames/2;

let currcolor = 255;

function setup() {
  createCanvas(canvasSize, canvasSize);
  for(let x=-1; x<nbSquares; x++) {
    let row = [];
    for(let y=0; y<nbSquares; y++) {
      let sq = new Quad(
        x*squareSize,
        y*squareSize,
        x*squareSize,
        (y+1)*squareSize,
        (x+1)*squareSize,
        (y+1)*squareSize,
        (x+1)*squareSize,
        y*squareSize,
        (x+y)%2,
        random()*maxDelay
      )
      row.push(sq);
    }
    squares.push(row);
  }
}

function draw() {
  background(255-currcolor)
  frameId = frameCount % nbFrames;
  
  for(let x=-1; x<nbSquares; x++) {
    for(let y=0; y<nbSquares; y++) {
      let sq = squares[x+1][y];
      progress = map(frameId, sq.delay, nbFrames-1-maxDelay+sq.delay, 0, 1, true);

      sq.x1 = (x+1)*squareSize - cos(progress * PI) * squareSize;
      sq.x2 = (x+1)*squareSize -cos(progress * PI) * squareSize;
      sq.y1 = y*squareSize - sin(progress * PI) * squareSize/8;
      sq.y2 = (y+1)*squareSize + sin(progress * PI) * squareSize/8;
    }
  }
  
  squares.flatMap(l => l).forEach(function(s) {
    s.render();
  });
  
  if(frameId == nbFrames-1)
  {
    currcolor = 255-currcolor;
    fill(currcolor);
    stroke(currcolor);
  }
}

function Quad(x1, y1, x2, y2, x3, y3, x4, y4, fake, delay) {
  this.x1 = x1;
  this.y1 = y1;
  this.x2 = x2;
  this.y2 = y2;
  this.x3 = x3;
  this.y3 = y3;
  this.x4 = x4;
  this.y4 = y4;
  this.fake = fake;
  this.delay = delay;
  //this.sqcolor = sqcolor;
  this.render = function() {
    if(this.fake){
      return;
    }
    
    strokeWeight(0.1);
    quad(this.x1, 
         this.y1,
         this.x2, 
         this.y2,
         this.x3, 
         this.y3,
         this.x4, 
         this.y4)
  }
}