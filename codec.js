/* The sheet code carries the choice: three objects and a task, written in base 31 with no letters
   that look alike. Each version fixes the list of objects and tasks it counts against, so a code made
   today still reads correctly after the case changes. build.py adds a version when the lists change.
   SM-   29 objects, order of picking kept, four characters.
   SM2-  100 objects, the three kept as a set (order dropped), five characters. */
const CODE_ABC='ABCDEFGHJKMNPQRSTUVWXYZ23456789';
const CODE_VERSIONS=/*__CODES__*/[];
const cC2=n=>n<2?0:n*(n-1)/2, cC3=n=>n<3?0:n*(n-1)*(n-2)/6;
function codeSpace(v){return (v.ordered?Math.pow(v.objects.length,3):cC3(v.objects.length))*v.tasks.length}
function encodeWith(v,ids,n){
  const no=v.objects.length,nt=v.tasks.length,idx=ids.map(id=>v.objects.indexOf(id)),t=v.tasks.indexOf(n);
  if(idx.length!==3||idx.some(i=>i<0)||t<0)return null;
  let x;
  if(v.ordered)x=((idx[0]*no+idx[1])*no+idx[2])*nt+t;
  else{const s=idx.slice().sort((a,b)=>a-b);if(s[0]===s[1]||s[1]===s[2])return null;x=(s[0]+cC2(s[1])+cC3(s[2]))*nt+t}
  let out='';for(let i=0;i<v.length;i++){out=CODE_ABC[x%31]+out;x=Math.floor(x/31)}
  return v.prefix+out;
}
function encodeSheet(ids,n){return encodeWith(CODE_VERSIONS[CODE_VERSIONS.length-1],ids,n)}
function decodeSheet(code){
  const c=String(code).toUpperCase().replace(/\s+/g,'');
  const vs=CODE_VERSIONS.slice().sort((a,b)=>b.prefix.length-a.prefix.length);
  for(const v of vs){
    const bare=v.prefix.replace(/-$/,'');let body=null;
    if(c.startsWith(v.prefix))body=c.slice(v.prefix.length);else if(c.startsWith(bare)&&c.length===bare.length+v.length)body=c.slice(bare.length);
    if(body===null||body.length!==v.length)continue;
    let x=0,ok=true;for(const ch of body){const k=CODE_ABC.indexOf(ch);if(k<0){ok=false;break}x=x*31+k}
    if(!ok||x>=codeSpace(v))return null;
    const nt=v.tasks.length,task=v.tasks[x%nt];let r=Math.floor(x/nt),idx;
    if(v.ordered){const no=v.objects.length;idx=[Math.floor(r/(no*no)),Math.floor(r/no)%no,r%no]}
    else{let s2=2;while(cC3(s2+1)<=r)s2++;r-=cC3(s2);let s1=1;while(cC2(s1+1)<=r)s1++;r-=cC2(s1);idx=[r,s1,s2]}
    return {objects:idx.map(i=>v.objects[i]),task,version:v.prefix};
  }
  return null;
}
