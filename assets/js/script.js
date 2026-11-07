const cv=document.getElementById('bg'),c=cv.getContext('2d'),still=matchMedia('(prefers-reduced-motion: reduce)').matches;
let W,H,mx=-1,my=-1;const fine=matchMedia('(pointer:fine)').matches;
function sz(){W=cv.width=innerWidth;H=cv.height=innerHeight}
function gear(x,y,r,t,a){const ro=r,ri=r*.84,w=Math.PI/t;c.beginPath();
 for(let i=0;i<t;i++){const b=a+i*2*w;c.lineTo(x+ri*Math.cos(b-w/2),y+ri*Math.sin(b-w/2));c.lineTo(x+ro*Math.cos(b-w/4),y+ro*Math.sin(b-w/4));c.lineTo(x+ro*Math.cos(b+w/4),y+ro*Math.sin(b+w/4));c.lineTo(x+ri*Math.cos(b+w/2),y+ri*Math.sin(b+w/2));c.arc(x,y,ri,b+w/2,b+1.5*w)}
 c.closePath();c.stroke();c.beginPath();c.arc(x,y,r*.22,0,7);c.stroke();c.beginPath();c.arc(x,y,r*.6,0,7);c.setLineDash([2,6]);c.stroke();c.setLineDash([])}
function frame(t){c.clearRect(0,0,W,H);
 c.strokeStyle='rgba(236,231,217,.07)';c.lineWidth=1;c.beginPath();for(let x=0;x<W;x+=32){c.moveTo(x,0);c.lineTo(x,H)}for(let y=0;y<H;y+=32){c.moveTo(0,y);c.lineTo(W,y)}c.stroke();
 const s=Math.min(W,H),r1=s*(W<700?.2:.24),t1=20,t2=12,r2=r1*.6,x1=W*(W<700?.72:.8),y1=H*.34,a1=(still?0:t*.0004)+scrollY*.002;
 const d=.92*(r1+r2),a2=Math.PI+Math.PI/t2-a1*t1/t2;
 c.strokeStyle='rgba(236,231,217,.34)';c.lineWidth=1.4;gear(x1,y1,r1,t1,a1);gear(x1+d,y1,r2,t2,a2);
 const r3=r1*.55,t3=14,t4=10,r4=r1*.36,x2=W*(W<700?.14:.16),y2=H*.78,a3=(still?0:t*.0003)-scrollY*.0015;
 const d2=.92*(r3+r4),a4=Math.PI+Math.PI/t4-a3*t3/t4;
 c.strokeStyle='rgba(236,231,217,.27)';gear(x2,y2,r3,t3,a3);gear(x2+d2,y2,r4,t4,a4);
 c.strokeStyle='rgba(255,90,43,.55)';c.setLineDash([14,4,2,4]);c.beginPath();c.moveTo(x1-r1*1.2,y1);c.lineTo(x1+d+r2*1.2,y1);c.moveTo(x1,y1-r1*1.2);c.lineTo(x1,y1+r1*1.2);c.stroke();c.setLineDash([]);
 c.fillStyle='rgba(236,231,217,.55)';c.font='11px IBM Plex Mono';c.fillText('Z=20',x1-14,y1+r1*1.3);c.fillText('Z=12',x1+d-14,y1+r2*1.5);
 if(fine&&mx>=0){c.strokeStyle='rgba(255,90,43,.5)';c.setLineDash([4,4]);c.beginPath();c.moveTo(mx,0);c.lineTo(mx,H);c.moveTo(0,my);c.lineTo(W,my);c.stroke();c.setLineDash([]);c.fillStyle='#ff5a2b';c.fillText(`X ${mx|0}  Y ${my|0}`,mx+8,my-8)}
 if(!still)requestAnimationFrame(frame)}
addEventListener('pointermove',e=>{mx=e.clientX;my=e.clientY;if(still)frame(0)});addEventListener('resize',()=>{sz();if(still)frame(0)});addEventListener('scroll',()=>{if(still)frame(0)});
sz();requestAnimationFrame(frame);
const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}}),{threshold:.1});document.querySelectorAll('.r').forEach(e=>io.observe(e));
document.getElementById('y').textContent=new Date().getFullYear();
