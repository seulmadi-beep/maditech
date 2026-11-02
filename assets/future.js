(()=>{'use strict';
const canvas=document.getElementById('future-scene');if(!canvas)return;const ctx=canvas.getContext('2d');if(!ctx)return;
const motion=matchMedia('(prefers-reduced-motion: reduce)');let w=0,h=0,visible=true,frame=0,t=0,px=0,py=0,targetX=0,targetY=0,last=0;
const hero=canvas.closest('.hero');
const particles=Array.from({length:55},(_,i)=>({x:Math.sin(i*32.7)*1.5,y:Math.cos(i*15.3)*1.2,z:Math.sin(i*4.9)*1.5}));
// Project points in a rotating three-dimensional coordinate system onto the canvas.
function project(x,y,z,angle){const a=angle+px*.2,b=.58+py*.13;const xx=x*Math.cos(a)+z*Math.sin(a),zz=-x*Math.sin(a)+z*Math.cos(a),yy=y*Math.cos(b)-zz*Math.sin(b),depth=y*Math.sin(b)+zz*Math.cos(b);const perspective=3.9/(3.9+depth);const size=Math.min(w<850?w*.34:w*.22,290);const cx=w<850?w*.5:(document.documentElement.dir==='rtl'?w*.25:w*.75),cy=w<850?260:h*.52;return{x:cx+xx*size*perspective,y:cy+yy*size*perspective,z:depth,scale:perspective}}
function line(points,color,width=1){ctx.beginPath();points.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke()}
function ring(radius,tilt,angle,color){const points=[];for(let i=0;i<=100;i++){const a=i/100*Math.PI*2;points.push(project(radius*Math.cos(a),radius*Math.sin(a)*Math.cos(tilt),radius*Math.sin(a)*Math.sin(tilt),angle))}line(points,color);for(let i=0;i<3;i++){const a=t*.35+i*Math.PI*2/3,p=project(radius*Math.cos(a),radius*Math.sin(a)*Math.cos(tilt),radius*Math.sin(a)*Math.sin(tilt),angle);ctx.beginPath();ctx.arc(p.x,p.y,2.3*p.scale,0,Math.PI*2);ctx.fillStyle='#9aefff';ctx.shadowColor='#65dcff';ctx.shadowBlur=12;ctx.fill();ctx.shadowBlur=0}}
function draw(now){frame=0;if(!visible||document.hidden)return;if(!motion.matches&&now-last<32){frame=requestAnimationFrame(draw);return}last=now;px+=(targetX-px)*.045;py+=(targetY-py)*.045;t=motion.matches?0:now*.00018;ctx.clearRect(0,0,w,h);
const mobile=w<850,cx=mobile?w*.5:(document.documentElement.dir==='rtl'?w*.25:w*.75),cy=mobile?260:h*.52;const glow=ctx.createRadialGradient(cx,cy,20,cx,cy,mobile?250:400);glow.addColorStop(0,'#3297dd12');glow.addColorStop(.55,'#5f75dd09');glow.addColorStop(1,'#00000000');ctx.fillStyle=glow;ctx.fillRect(0,0,w,h);
// Orbital architecture and a wireframe floor: depth remains visible around the portrait.
ring(1.2,.35,t,'#6ce5ff32');ring(1.3,1.4,-t*.7,'#a58dff40');ring(1.05,2.3,t*.5,'#63aaff27');
for(let i=-6;i<=6;i++){const points=[];for(let j=-6;j<=6;j++)points.push(project(i*.23,1.05,j*.23,t*.12));line(points,'#6bcfff12');const other=[];for(let j=-6;j<=6;j++)other.push(project(j*.23,1.05,i*.23,t*.12));line(other,'#6bcfff12')}
const vertices=[];for(let i=0;i<12;i++){const a=i/12*Math.PI*2;vertices.push(project(Math.cos(a)*1.15,Math.sin(a)*.82,Math.sin(a*2+t)*.3,t*.35))}for(let i=0;i<12;i++){line([vertices[i],vertices[(i+1)%12]],'#8ae6ff22');if(i%3===0)line([vertices[i],vertices[(i+4)%12]],'#8e9fff16')}
for(const p of particles){const q=project(p.x,p.y,p.z,t*.25);ctx.globalAlpha=Math.max(.1,Math.min(.65,(2-q.z)*.2));ctx.beginPath();ctx.arc(q.x,q.y,1.1*q.scale,0,Math.PI*2);ctx.fillStyle='#a5e7ff';ctx.fill()}ctx.globalAlpha=1;
if(!motion.matches)frame=requestAnimationFrame(draw)}
function start(){if(!frame&&visible&&!document.hidden)frame=requestAnimationFrame(draw)}
function resize(){const r=hero.getBoundingClientRect();w=r.width;h=r.height;const ratio=Math.min(devicePixelRatio||1,1.5);canvas.width=Math.round(w*ratio);canvas.height=Math.round(h*ratio);ctx.setTransform(ratio,0,0,ratio,0,0);start()}
new ResizeObserver(resize).observe(hero);new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;if(visible)start();else{cancelAnimationFrame(frame);frame=0}},{threshold:0}).observe(hero);
hero.addEventListener('pointermove',e=>{if(e.pointerType==='touch')return;const r=hero.getBoundingClientRect();targetX=(e.clientX-r.left)/r.width-.5;targetY=(e.clientY-r.top)/r.height-.5;start()},{passive:true});hero.addEventListener('pointerleave',()=>{targetX=0;targetY=0});document.addEventListener('visibilitychange',()=>{if(document.hidden){cancelAnimationFrame(frame);frame=0}else start()});motion.addEventListener('change',()=>{cancelAnimationFrame(frame);frame=0;start()});new MutationObserver(start).observe(document.documentElement,{attributes:true,attributeFilter:['dir']});resize();
})();
