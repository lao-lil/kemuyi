// Service Worker — 科目一 PWA
// 缓存版本随构建注入，更新时自动清理旧缓存
var CACHE_VER = "kemuyi-__BUILD_VER__";
var SHELL_CACHE = CACHE_VER + "-shell";
var IMG_CACHE = "kemuyi-imgs";

// 预缓存的应用壳文件
var SHELL_FILES = [
  "./",
  "./index.html",
  "./manifest.json",
  "./icon-192.png",
  "./icon-512.png"
];

self.addEventListener("install", function(e){
  e.waitUntil(
    caches.open(SHELL_CACHE).then(function(cache){
      // 逐个缓存，单文件失败不阻塞
      return Promise.all(SHELL_FILES.map(function(url){
        return cache.add(url).catch(function(){ /* 忽略单文件失败 */ });
      }));
    }).then(function(){
      return self.skipWaiting();
    })
  );
});

self.addEventListener("activate", function(e){
  e.waitUntil(
    caches.keys().then(function(keys){
      return Promise.all(keys.map(function(key){
        // 清理旧版本 shell 缓存（保留图片缓存 kemuyi-imgs）
        if(key.indexOf("kemuyi-") === 0 && key !== SHELL_CACHE && key !== IMG_CACHE){
          return caches.delete(key);
        }
      }));
    }).then(function(){
      return self.clients.claim();
    })
  );
});

self.addEventListener("fetch", function(e){
  var req = e.request;
  var url = new URL(req.url);

  // 仅处理 GET
  if(req.method !== "GET") return;

  // 图片请求：cache-first（懒缓存核心）
  var isImg = req.destination === "image" || /\.(jpg|jpeg|png|gif|webp)(\?|$)/i.test(url.pathname);
  if(isImg && url.origin !== self.location.origin){
    e.respondWith(imgCacheFirst(req));
    return;
  }

  // 同源导航/静态资源：stale-while-revalidate
  if(url.origin === self.location.origin){
    e.respondWith(shellSWR(req));
    return;
  }
  // 其他跨域请求：直接放行（不缓存）
});

function imgCacheFirst(req){
  return caches.open(IMG_CACHE).then(function(cache){
    return cache.match(req).then(function(cached){
      if(cached) return cached;
      return fetch(req).then(function(resp){
        // 缓存成功的图片响应
        if(resp && (resp.ok || resp.type === "opaque")){
          cache.put(req, resp.clone()).catch(function(){});
        }
        return resp;
      }).catch(function(){
        // 离线且无缓存：返回透明占位，避免破图
        return new Response("", {status:204});
      });
    });
  });
}

function shellSWR(req){
  return caches.open(SHELL_CACHE).then(function(cache){
    return cache.match(req).then(function(cached){
      var fetchPromise = fetch(req).then(function(resp){
        if(resp && resp.ok && (req.mode !== "navigate" || resp.type !== "opaqueredirect")){
          cache.put(req, resp.clone()).catch(function(){});
        }
        return resp;
      }).catch(function(){
        // 离线：导航请求回退到缓存的 index.html
        if(req.mode === "navigate"){
          return cache.match("./index.html").then(function(r){ return r || cached; });
        }
        return cached;
      });
      return cached || fetchPromise;
    });
  });
}

// 接收页面消息：清除图片缓存
self.addEventListener("message", function(e){
  if(e.data === "clear-img-cache"){
    caches.delete(IMG_CACHE).then(function(){
      e.source && e.source.postMessage({type:"img-cache-cleared"});
    });
  }
});
