/* The sheet code carries the choice: the three objects in the order picked and the task.
   Objects are counted in order of their number, tasks by their number, then written in base 31
   with no letters that look alike. 29 x 29 x 29 x 30 choices fit in four characters.
   Version 1 codes start "SM-"; if the objects or tasks ever change, the next version starts "SM2-". */
const CODE_ABC='ABCDEFGHJKMNPQRSTUVWXYZ23456789';
const CODE_OBJ=D.objects.map(o=>o.id).sort((a,b)=>a-b), CODE_TASK=D.tasks.map(t=>t.n).sort((a,b)=>a-b);
function encodeSheet(ids,n){
  const no=CODE_OBJ.length,nt=CODE_TASK.length;
  let v=((CODE_OBJ.indexOf(ids[0])*no+CODE_OBJ.indexOf(ids[1]))*no+CODE_OBJ.indexOf(ids[2]))*nt+CODE_TASK.indexOf(n);
  let s='';for(let i=0;i<4;i++){s=CODE_ABC[v%31]+s;v=Math.floor(v/31)}return 'SM-'+s;
}
function decodeSheet(code){
  const c=String(code).toUpperCase().replace(/\s+/g,'').replace(/^SM-?/,'');
  if(c.length!==4)return null;let v=0;
  for(const ch of c){const k=CODE_ABC.indexOf(ch);if(k<0)return null;v=v*31+k}
  const no=CODE_OBJ.length,nt=CODE_TASK.length;if(v>=no*no*no*nt)return null;
  const task=CODE_TASK[v%nt];v=Math.floor(v/nt);const c3=CODE_OBJ[v%no];v=Math.floor(v/no);const c2=CODE_OBJ[v%no];const c1=CODE_OBJ[Math.floor(v/no)];
  return {objects:[c1,c2,c3],task};
}