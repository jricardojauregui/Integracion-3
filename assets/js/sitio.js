/* =============================================================================
   Comportamiento común del sitio:
   - barra de navegación (borde y título compacto al desplazar)
   - acordeón de archivos de código: abrir/cerrar, copiar al portapapeles
   - índice lateral que resalta la sección visible
   ============================================================================= */
(function () {
  "use strict";

  /* --- Navegación -------------------------------------------------------- */
  function iniciarNav() {
    var nav = document.querySelector(".nav");
    if (!nav) return;
    function revisar() { nav.classList.toggle("desplazada", window.scrollY > 24); }
    revisar();
    window.addEventListener("scroll", revisar, { passive: true });

    var pagina = document.body.getAttribute("data-pagina");
    Array.prototype.forEach.call(nav.querySelectorAll("[data-nav]"), function (enlace) {
      if (enlace.getAttribute("data-nav") === pagina) {
        enlace.setAttribute("aria-current", "page");
      }
    });
  }

  /* --- Acordeón de código ------------------------------------------------ */
  function alternar(bloque, forzar) {
    var abierto = forzar !== undefined ? forzar : !bloque.classList.contains("abierto");
    bloque.classList.toggle("abierto", abierto);
    var boton = bloque.querySelector(".codigo__abrir");
    if (boton) boton.setAttribute("aria-expanded", abierto ? "true" : "false");
  }

  function iniciarCodigo() {
    Array.prototype.forEach.call(document.querySelectorAll(".codigo"), function (bloque) {
      var boton = bloque.querySelector(".codigo__abrir");
      if (boton) {
        boton.addEventListener("click", function () { alternar(bloque); });
      }

      var copiar = bloque.querySelector("[data-copiar]");
      if (copiar) {
        copiar.addEventListener("click", function () {
          var fuente = bloque.querySelector(".codigo__fuente code");
          if (!fuente) return;
          var texto = Array.prototype.map.call(fuente.querySelectorAll(".l"), function (linea) {
            return linea.textContent;
          }).join("\n");

          var etiqueta = copiar.querySelector("span");
          var original = etiqueta ? etiqueta.textContent : "";

          function confirmar(ok) {
            copiar.classList.toggle("hecho", ok);
            if (etiqueta) etiqueta.textContent = ok ? "Copiado" : "Error";
            setTimeout(function () {
              copiar.classList.remove("hecho");
              if (etiqueta) etiqueta.textContent = original;
            }, 1800);
          }

          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(texto).then(function () { confirmar(true); },
                                                      function () { confirmar(false); });
          } else {
            // Respaldo para navegadores sin API de portapapeles o sin HTTPS
            var area = document.createElement("textarea");
            area.value = texto;
            area.setAttribute("readonly", "");
            area.style.position = "fixed";
            area.style.opacity = "0";
            document.body.appendChild(area);
            area.select();
            var ok = false;
            try { ok = document.execCommand("copy"); } catch (err) { ok = false; }
            document.body.removeChild(area);
            confirmar(ok);
          }
        });
      }
    });

    // Botones "expandir todo" / "contraer todo" por sección
    Array.prototype.forEach.call(document.querySelectorAll("[data-expandir]"), function (boton) {
      boton.addEventListener("click", function () {
        var lista = document.getElementById(boton.getAttribute("data-expandir"));
        if (!lista) return;
        var abrir = boton.getAttribute("data-estado") !== "abierto";
        Array.prototype.forEach.call(lista.querySelectorAll(".codigo"), function (b) {
          alternar(b, abrir);
        });
        boton.setAttribute("data-estado", abrir ? "abierto" : "cerrado");
        var etiqueta = boton.querySelector("span");
        if (etiqueta) etiqueta.textContent = abrir ? "Contraer todo" : "Expandir todo";
      });
    });
  }

  /* --- Índice lateral ---------------------------------------------------- */
  function iniciarIndice() {
    var indice = document.querySelector(".indice");
    if (!indice || !("IntersectionObserver" in window)) return;

    var enlaces = Array.prototype.slice.call(indice.querySelectorAll("a"));
    var secciones = enlaces.map(function (a) {
      return document.getElementById(a.getAttribute("href").slice(1));
    }).filter(Boolean);
    if (!secciones.length) return;

    var visibles = new Set();

    function marcar() {
      var actual = secciones.find(function (s) { return visibles.has(s.id); });
      enlaces.forEach(function (a) {
        a.classList.toggle("activo", !!actual && a.getAttribute("href") === "#" + actual.id);
      });
    }

    var observador = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (e) {
        if (e.isIntersecting) visibles.add(e.target.id);
        else visibles.delete(e.target.id);
      });
      marcar();
    }, { rootMargin: "-70px 0px -70% 0px" });

    secciones.forEach(function (s) { observador.observe(s); });
  }

  document.addEventListener("DOMContentLoaded", function () {
    iniciarNav();
    iniciarCodigo();
    iniciarIndice();
    if (window.Visor) window.Visor.conectar(document);

    var anio = document.querySelector("[data-anio]");
    if (anio) anio.textContent = new Date().getFullYear();
  });
})();