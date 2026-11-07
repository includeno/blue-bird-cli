'use strict';
const strings = {
  en: {
    local:'Local only',eyebrow:'PERMISSIONS, WITH BOUNDARIES',heading:'Give each agent its own scope.',"subtitle":"Choose which CLI functions each agent can use, and which Bluebird tags it can access.",refresh:'Refresh',created:'CODE CREATED',saveCode:'Save this code now.',once:'The full code is shown only once. It cannot be recovered after you leave this page.',codeLabel:'New authorization code',copy:'Copy code',hide:'Hide',active:'Active codes',activeNote:'Ready for scoped CLI access',"tags":"List authorized tags",tagsNote:'Read from your local Bluebird app',rule:'Scope rule',allTags:'Every tag must match',ruleNote:'Untagged tasks are never included.',codes:'Authorization codes',codesNote:'Changes apply when the next CLI command starts.',"newScope":"NEW AUTHORIZATION",createTitle:'Create an access code',nameLabel:'Name',namePlaceholder:'e.g. Codex · Work',chooseTags:'Authorized tags',atLeast:'Select at least one existing tag.',searchPlaceholder:'Find a tag…',createButton:'Generate code',cancel:'Cancel',scopeTitle:'A precise boundary',scopeNote:'A task needs at least one tag, and all its tags must belong to this code. Codes bind to tag IDs, so recreating a tag with the same name does not inherit access.',connect:'CONNECT YOUR AGENT',useTitle:'Two ways to run the CLI.',scoped:'Scoped access',envNote:'Pass the code using an environment variable or --code. Keep the value out of shared logs.',owner:'Local owner',fullNote:'Explicit unrestricted access, including this authorization console.',boundary:'Codes scope CLI commands. A local user who can run full-access or read app data directly remains unrestricted; this is not an operating-system sandbox.',noCodes:'No codes yet',"noCodesNote":"Choose a name, tags and allowed CLI functions to create your first code.",noTags:'No tags available. Create a tag in Bluebird, then refresh.',noMatches:'No matching tags.',selected:'{n} tag(s) selected',activeState:'Active',revoked:'Revoked',"edit":"Edit permissions",revoke:'Revoke',revokeAsk:'Revoke “{name}”? The next command using this code will be denied.',deletedTag:'deleted tag',"editTitle":"Edit code permissions","editScope":"EDIT PERMISSIONS",save:'Save changes',"saved":"Permissions updated. The existing code uses these settings on its next command.",revokedNotice:'Code revoked.',copied:'Code copied.',copyFailed:'Select the code and copy it manually.',locked:'Open the private URL printed by bluebird start web. The admin session is kept only in this page; reopening or refreshing needs that URL again.',failed:'Request failed',"required":"Choose at least one tag and one CLI function.",loading:'Loading local permissions…',createdAt:'Created',noStorage:'Local data unavailable. Run bluebird --full-access doctor in the terminal.',"functions":"Allowed CLI functions","functionsHint":"Choose at least one function. Tag scope applies to every selected operation.","selectAll":"Select all","clearAll":"Clear","functionsSelected":"{n} of {total} functions selected","read":"Queries","tasks":"Task operations","timer":"Timer controls","list":"List tasks","get":"Read task details","logs":"Read focus logs","add":"Create tasks","update":"Edit tasks","complete":"Complete tasks","reopen":"Reopen tasks","delete":"Delete tasks","timer.status":"Read timer status","timer.start":"Start timer","timer.stop":"Stop timer","timer.finish":"Finish session","timer.reset":"Reset timer","noFunctions":"No functions granted"
  },
  'zh-CN': {
    local:'仅本机访问',eyebrow:'让权限有明确边界',heading:'为每个 Agent 划定范围。',"subtitle":"分别指定 Agent 可以使用哪些 CLI 功能，以及可以访问哪些 Bluebird 标签。",refresh:'刷新',created:'授权已创建',saveCode:'现在保存这份 code。',once:'完整 code 仅显示一次，离开页面后无法找回。',codeLabel:'新授权 code',copy:'复制 code',hide:'隐藏',active:'有效授权',activeNote:'可用于指定范围的 CLI 调用',"tags":"查询授权标签",tagsNote:'从本机 Bluebird 读取',rule:'任务权限规则',allTags:'全部标签均须匹配',ruleNote:'不包含没有标签的任务。',codes:'授权 code',codesNote:'撤销或范围变更从下一条 CLI 命令起生效。',"newScope":"创建授权",createTitle:'生成新的授权 code',nameLabel:'授权名称',namePlaceholder:'例如：Codex · 工作任务',chooseTags:'允许访问的标签',atLeast:'至少选择一个现有标签。',searchPlaceholder:'搜索标签…',createButton:'生成 code',cancel:'取消',scopeTitle:'清晰的任务边界',scopeNote:'任务至少有一个标签，且全部标签都必须在授权范围内。code 绑定标签 ID，同名标签删除重建后不会继承权限。',connect:'连接你的 AGENT',useTitle:'两种 CLI 启动方式。',scoped:'使用授权 code',envNote:'通过环境变量或 --code 传入授权。请勿把完整值写入共享日志。',owner:'本机所有者模式',fullNote:'显式开放全部操作权限，包括这个授权管理页面。',boundary:'code 限制 CLI 命令的访问范围。本机用户仍可选择 full-access 或直接读取 App 数据；此功能不替代操作系统沙箱。',noCodes:'还没有授权 code',"noCodesNote":"填写名称，选择标签和允许使用的 CLI 功能，创建第一份授权。",noTags:'暂无标签。请先在 Bluebird 创建标签，再刷新。',noMatches:'没有匹配的标签。',selected:'已选择 {n} 个标签',activeState:'有效',revoked:'已撤销',"edit":"设置权限",revoke:'撤销',revokeAsk:'撤销“{name}”？使用此 code 的下一条命令将被拒绝。',deletedTag:'标签已删除',"editTitle":"修改 code 权限","editScope":"编辑功能与范围",save:'保存更改',"saved":"功能权限与标签范围已更新，原 code 的下一条命令起生效。",revokedNotice:'授权已撤销。',copied:'code 已复制。',copyFailed:'请选中 code 手动复制。',locked:'请打开 bluebird start web 输出的专用地址。管理员会话只保存在当前页面，重新打开或刷新页面需要再次使用该地址。',failed:'请求失败',"required":"至少选择一个标签和一项 CLI 功能。",loading:'正在读取本机授权…',createdAt:'创建于',noStorage:'本地数据不可用，请在终端运行 bluebird --full-access doctor。',"functions":"可使用的 CLI 功能","functionsHint":"至少选择一项功能。所有操作仍受所选标签范围限制。","selectAll":"全部选择","clearAll":"全部清空","functionsSelected":"已选择 {n} / {total} 项功能","read":"查询功能","tasks":"任务增删改","timer":"计时控制","list":"查询任务列表","get":"读取任务详情","logs":"查询专注记录","add":"创建任务","update":"修改任务","complete":"完成任务","reopen":"恢复任务","delete":"删除任务","timer.status":"查询计时状态","timer.start":"开始计时","timer.stop":"停止计时","timer.finish":"完成本轮计时","timer.reset":"重置计时","noFunctions":"尚未授予功能权限"
  },
  ja: {
    local:'この Mac のみ',eyebrow:'権限の範囲を明確に',heading:'エージェントごとに操作範囲を。',"subtitle":"エージェントが使える CLI 機能と、アクセスできる Bluebird タグを個別に設定します。",refresh:'更新',created:'コードを作成しました',saveCode:'このコードを保存してください。',once:'完全なコードは一度だけ表示されます。ページを離れると再取得できません。',codeLabel:'新しい認証コード',copy:'コピー',hide:'非表示',active:'有効なコード',activeNote:'指定範囲で CLI を操作できます',"tags":"許可タグ一覧",tagsNote:'この Mac の Bluebird から取得',rule:'アクセス条件',allTags:'すべてのタグが対象内',ruleNote:'タグのないタスクは含まれません。',codes:'認証コード',codesNote:'変更や失効は次の CLI コマンドから適用されます。',"newScope":"新しい認証",createTitle:'認証コードを作成',nameLabel:'名前',namePlaceholder:'例：Codex · 仕事',chooseTags:'許可するタグ',atLeast:'既存のタグを一つ以上選択してください。',searchPlaceholder:'タグを検索…',createButton:'コードを生成',cancel:'キャンセル',scopeTitle:'タスクの範囲を限定',scopeNote:'タスクには一つ以上のタグが必要で、すべて許可範囲内である必要があります。タグ ID に紐付くため、同名タグを作り直しても権限は引き継がれません。',connect:'エージェントに接続',useTitle:'CLI を使う二つの方法。',scoped:'認証コードを使う',envNote:'環境変数または --code で渡します。完全な値を共有ログに残さないでください。',owner:'この Mac の所有者',fullNote:'この管理画面を含む、制限のない操作を明示的に許可します。',boundary:'コードは CLI のアクセス範囲を制限します。full-access の実行やアプリデータの直接読み取りが可能なローカルユーザーは制限されません。OS のサンドボックスではありません。',noCodes:'コードはまだありません',"noCodesNote":"名前、タグ、許可する CLI 機能を選んで作成してください。",noTags:'タグがありません。Bluebird でタグを作成してから更新してください。',noMatches:'一致するタグがありません。',selected:'{n} 個のタグを選択中',activeState:'有効',revoked:'失効済み',"edit":"権限を設定",revoke:'失効',revokeAsk:'「{name}」を失効させますか？ このコードの次のコマンドは拒否されます。',deletedTag:'削除済みタグ',"editTitle":"コードの権限を編集","editScope":"機能と範囲を編集",save:'変更を保存',"saved":"権限を更新しました。既存コードの次のコマンドから適用されます。",revokedNotice:'コードを失効させました。',copied:'コードをコピーしました。',copyFailed:'コードを選択して手動でコピーしてください。',locked:'bluebird start web が出力した専用 URL を開いてください。管理セッションはこのページだけに保持されるため、再表示や再読み込みには同じ URL が必要です。',failed:'リクエストに失敗しました',"required":"タグと CLI 機能をそれぞれ一つ以上選択してください。",loading:'ローカルの権限を読み込み中…',createdAt:'作成',noStorage:'ローカルデータを利用できません。ターミナルで bluebird --full-access doctor を実行してください。',"functions":"利用できる CLI 機能","functionsHint":"機能を一つ以上選択してください。すべての操作にタグの範囲が適用されます。","selectAll":"すべて選択","clearAll":"すべて解除","functionsSelected":"{total} 機能中 {n} 個を選択","read":"照会","tasks":"タスク操作","timer":"タイマー操作","list":"タスク一覧","get":"タスク詳細","logs":"集中記録の照会","add":"タスク作成","update":"タスク編集","complete":"タスク完了","reopen":"タスク再開","delete":"タスク削除","timer.status":"状態の照会","timer.start":"開始","timer.stop":"停止","timer.finish":"セッション完了","timer.reset":"リセット","noFunctions":"機能は許可されていません"
  }
};
strings.en.availableTags='Available tags';strings['zh-CN'].availableTags='可用标签';strings.ja.availableTags='利用可能なタグ';
Object.assign(strings["en"],{"home": "Home", "codeList": "Authorization codes", "newCode": "New code", "manageCodes": "Manage authorization codes", "homeHint": "Choose functions, bind tags, and give each agent its own code.", "listHeading": "Authorization codes", "listSubtitle": "Review each code’s functions and tags. Create, edit, or revoke access here.", "close": "Close dialog"});
Object.assign(strings["zh-CN"],{"home": "首页", "codeList": "授权列表", "newCode": "新增授权", "manageCodes": "管理授权 code", "homeHint": "选择功能、绑定标签，为每个 Agent 分配独立授权。", "listHeading": "授权列表", "listSubtitle": "查看每份 code 的功能与标签范围，在此新增、修改或撤销授权。", "close": "关闭弹窗"});
Object.assign(strings["ja"],{"home": "ホーム", "codeList": "認証コード一覧", "newCode": "新規作成", "manageCodes": "認証コードを管理", "homeHint": "機能とタグを選択し、エージェントごとにコードを発行します。", "listHeading": "認証コード一覧", "listSubtitle": "コードごとの機能とタグを確認し、作成・編集・失効を管理します。", "close": "ダイアログを閉じる"});
const $ = id => document.getElementById(id);
const initial = new URLSearchParams(location.hash.slice(1));
const token = initial.get('token') || '';
history.replaceState(null, '', location.pathname);
let language = navigator.language.startsWith('zh') ? 'zh-CN' : navigator.language.startsWith('ja') ? 'ja' : 'en';
try { if (strings[localStorage.getItem('bluebird.language')]) language = localStorage.getItem('bluebird.language'); } catch (_) {}
let state = {tags:[],codes:[]}, selected = new Set(), functions = new Set(), editing = null, busy = false, loaded = false;
const t = (key, values={}) => Object.entries(values).reduce((s,[k,v])=>s.replaceAll(`{${k}}`,String(v)),strings[language][key] || key);
function el(tag, className, text) { const node=document.createElement(tag);if(className)node.className=className;if(text!==undefined)node.textContent=text;return node; }
function hideCode(){$('new-code').value='';$('secret-panel').hidden=true;}
window.addEventListener('pagehide',hideCode);
function notice(message, success=false) { const target=$('code-dialog').open&&!success?$('form-notice'):$('notice');target.textContent=message;target.className='notice'+(success?' success':'');target.hidden=!message; }
async function api(path, method='GET', payload) {
  const response = await fetch(path,{method,headers:{Authorization:`Bearer ${token}`,...(payload?{'Content-Type':'application/json'}:{})},...(payload?{body:JSON.stringify(payload)}:{})});
  const result=await response.json();
  if(!response.ok || !result.ok)throw new Error(response.status===401?t('locked'):response.status===503?t('noStorage'):result.error?.message||t('failed'));
  return result.data;
}
function formState() { $('close-dialog').disabled=busy;$('cancel-edit').disabled=busy;$('save').disabled=busy||!loaded||!selected.size||!functions.size;$('selection-count').textContent=t('selected',{n:selected.size});$('form-title').textContent=t(editing?'editTitle':'createTitle');$('form-kicker').textContent=t(editing?'editScope':'newScope');$('save').textContent=t(editing?'save':'createButton'); }
function renderPicker() {
  const target=$('tag-picker');target.replaceChildren();const term=$('tag-search').value.toLocaleLowerCase();
  const tags=state.tags.filter(tag=>tag.name.toLocaleLowerCase().includes(term));
  if(!tags.length)target.append(el('p','field-hint',t(state.tags.length?'noMatches':'noTags')));
  for(const tag of tags){const label=el('label','tag-option');const checkbox=el('input');checkbox.type='checkbox';checkbox.value=tag.id;checkbox.checked=selected.has(tag.id);checkbox.addEventListener('change',()=>{checkbox.checked?selected.add(tag.id):selected.delete(tag.id);formState();});label.append(checkbox,el('span',null,tag.name||`ID: ${tag.id}`));label.title=`ID: ${tag.id}`;target.append(label);}formState();
}
function renderPermissions() {
  const picker=$('permission-picker');picker.replaceChildren();
  const groups=state.permission_groups||{};
  for(const [group, permissions] of Object.entries(groups)) {
    const fieldset=el('fieldset','permission-group'),legend=el('legend'),label=el('label','group-option'),all=el('input');
    all.type='checkbox';all.dataset.group=group;
    const count=permissions.filter(permission=>functions.has(permission)).length;
    all.checked=count===permissions.length;all.indeterminate=count>0&&count<permissions.length;
    all.addEventListener('change',()=>{for(const permission of permissions)all.checked?functions.add(permission):functions.delete(permission);syncPermissions();});
    label.append(all,el('span',null,t(group)),el('small',null,`${count}/${permissions.length}`));legend.append(label);fieldset.append(legend);
    for(const permission of permissions){const option=el('label','permission-option'),checkbox=el('input');checkbox.type='checkbox';checkbox.value=permission;checkbox.checked=functions.has(permission);checkbox.addEventListener('change',()=>{checkbox.checked?functions.add(permission):functions.delete(permission);syncPermissions();});const name=el('span');name.append(el('span',null,t(permission)),el('code',null,permission.replace('.', ' ')));option.append(checkbox,name);fieldset.append(option);}
    picker.append(fieldset);
  }
  syncPermissions();
}
function syncPermissions(){
  const groups=state.permission_groups||{};
  for(const checkbox of $('permission-picker').querySelectorAll('input')){
    if(checkbox.dataset.group){const group=groups[checkbox.dataset.group],count=group.filter(item=>functions.has(item)).length;checkbox.checked=count===group.length;checkbox.indeterminate=count>0&&count<group.length;checkbox.parentElement.querySelector('small').textContent=`${count}/${group.length}`;}
    else checkbox.checked=functions.has(checkbox.value);
  }
  $('permission-count').textContent=t('functionsSelected',{n:functions.size,total:Object.values(groups).flat().length});formState();
}
function renderCodes() {
  const list=$('code-list');list.replaceChildren();
  if(!loaded){list.append(el('div','empty',t(token?'loading':'locked')));return;}
  if(!state.codes.length){const empty=el('div','empty');empty.append(el('strong',null,t('noCodes')),el('span',null,t('noCodesNote')));list.append(empty);}
  const tags=new Map(state.tags.map(tag=>[tag.id,tag.name]));
  for(const code of state.codes){const card=el('article','code-card'+(code.revoked_at?' revoked':''));const heading=el('div','card-heading');heading.append(el('h3',null,code.label),el('span','card-state',t(code.revoked_at?'revoked':'activeState')));card.append(heading,el('p','meta',`${t('createdAt')} ${new Date(code.created_at).toLocaleString(language)} · ${code.id.slice(0,8)}`));const chips=el('div','chips');for(const tag of code.tags){chips.append(el('span','chip'+(tags.has(tag.id)?'':' missing'),tags.has(tag.id)?`# ${tags.get(tag.id)}`:`# ${tag.name} · ${t('deletedTag')}`));}card.append(chips);
    const details=el('details','function-summary'),summary=el('summary',null,t('functionsSelected',{n:code.permissions.length,total:Object.values(state.permission_groups).flat().length})),allowed=el('div','chips');details.append(summary);for(const permission of code.permissions)allowed.append(el('span','chip',`${t(permission)} · ${permission.replace('.', ' ')}`));if(!code.permissions.length)allowed.append(el('span','field-hint',t('noFunctions')));details.append(allowed);card.append(details);
    if(!code.revoked_at){const actions=el('div','card-actions');const edit=el('button','secondary',t('edit'));edit.addEventListener('click',()=>{hideCode();$('form-notice').hidden=true;editing=code.id;functions=new Set(code.permissions);selected=new Set(code.tags.map(tag=>tag.id).filter(id=>tags.has(id)));$('label').value=code.label;$('tag-search').value='';renderPicker();renderPermissions();$('code-dialog').showModal();$('label').focus();});const revoke=el('button','danger',t('revoke'));revoke.addEventListener('click',async()=>{if(!confirm(t('revokeAsk',{name:code.label})))return;revoke.disabled=true;try{await api(`/api/codes/${code.id}/revoke`,'POST',{});hideCode();if(editing===code.id)resetForm();await refresh();notice(t('revokedNotice'),true);}catch(error){notice(error.message);revoke.disabled=false;}});actions.append(edit,revoke);card.append(actions);}list.append(card);
  }
  $('active-count').textContent=state.codes.filter(code=>!code.revoked_at).length;$('tag-count').textContent=state.tags.length;
}
function resetForm(){$('form-notice').hidden=true;editing=null;selected.clear();functions.clear();$('code-form').reset();renderPicker();renderPermissions();}
async function refresh(){if(!token){notice(t('locked'));return;}$('refresh').disabled=true;try{state=await api('/api/state');loaded=true;const ids=new Set(state.tags.map(tag=>tag.id));selected=new Set([...selected].filter(id=>ids.has(id)));renderCodes();renderPicker();renderPermissions();}catch(error){notice(error.message);}finally{$('refresh').disabled=false;}}
function navigate(path, push=true){
  const list=path==='/codes';
  if(push){hideCode();history.pushState(null,'',list?'/codes':'/');}
  $('home-page').hidden=list;$('codes-page').hidden=!list;
  $('page-heading').textContent=t(list?'listHeading':'heading');$('page-subtitle').textContent=t(list?'listSubtitle':'subtitle');
  document.querySelectorAll('nav [data-route]').forEach(link=>{if(link.dataset.route===(list?'/codes':'/'))link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');});
  document.title=`Bluebird · ${t(list?'codeList':'home')}`;
}
document.querySelectorAll('[data-route]').forEach(link=>link.addEventListener('click',event=>{if(event.button||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;event.preventDefault();navigate(link.dataset.route);window.scrollTo(0,0);}));
window.addEventListener('popstate',()=>{hideCode();navigate(location.pathname,false);});
function localize(){document.documentElement.lang=language;$('language').value=language;document.querySelectorAll('[data-i18n]').forEach(node=>node.textContent=t(node.dataset.i18n));document.querySelectorAll('[data-placeholder]').forEach(node=>node.placeholder=t(node.dataset.placeholder));renderCodes();renderPicker();renderPermissions();navigate(location.pathname,false);$('close-dialog').setAttribute('aria-label',t('close'));if(!token)notice(t('locked'));}
$('language').addEventListener('change',()=>{language=$('language').value;try{localStorage.setItem('bluebird.language',language);}catch(_){}localize();});
$('select-functions').addEventListener('click',()=>{functions=new Set(Object.values(state.permission_groups||{}).flat());renderPermissions();});
$('clear-functions').addEventListener('click',()=>{functions.clear();renderPermissions();});
$('tag-search').addEventListener('input',renderPicker);
$('refresh').addEventListener('click',()=>{hideCode();notice('');refresh();});
$('new-code-button').addEventListener('click',()=>{hideCode();resetForm();$('code-dialog').showModal();$('label').focus();});
$('cancel-edit').addEventListener('click',()=>$('code-dialog').close());
$('close-dialog').addEventListener('click',()=>$('code-dialog').close());
$('code-dialog').addEventListener('close',resetForm);
$('code-dialog').addEventListener('cancel',event=>{if(busy)event.preventDefault();});
$('code-form').addEventListener('submit',async event=>{event.preventDefault();if(!selected.size||!functions.size){notice(t('required'));return;}if(busy)return;busy=true;formState();notice('');const wasEditing=editing;try{const result=await api(editing?`/api/codes/${editing}`:'/api/codes',editing?'PATCH':'POST',{label:$('label').value,tag_ids:[...selected],permissions:[...functions]});if(result.code){$('new-code').value=result.code;$('secret-panel').hidden=false;$('secret-panel').scrollIntoView({behavior:'smooth',block:'center'});}$('code-dialog').close();await refresh();if(wasEditing)notice(t('saved'),true);}catch(error){notice(error.message);}finally{busy=false;formState();}});
$('copy-code').addEventListener('click',async()=>{try{await navigator.clipboard.writeText($('new-code').value);notice(t('copied'),true);}catch(_){$('new-code').select();notice(t('copyFailed'));}});
$('hide-code').addEventListener('click',hideCode);
localize();refresh();
