async function loadPurchases() {
  const status = $("#purchaseStatus");
  const { ok, status: responseStatus, data } = await api("/api/mis-compras");
  if (responseStatus === 401) {
    window.location.assign("/");
    return;
  }
  if (!ok) {
    status.textContent = data.error || "No pudimos cargar tus boletas.";
    return;
  }

  const purchases = data.compras ?? [];
  if (!purchases.length) {
    status.textContent = "Todavía no tienes boletas. Cuando confirmes una compra, aparecerá aquí.";
    return;
  }

  $("#purchasesBody").innerHTML = purchases.map(purchase => `
    <tr>
      <td>#${purchase.id}<small>${esc(purchase.comprada)}</small></td>
      <td><strong>${esc(purchase.pelicula)}</strong><small>${esc(purchase.formato)}</small></td>
      <td>${esc(purchase.fecha)} · ${esc(purchase.hora)}<small>${esc(purchase.sede)} · ${esc(purchase.ciudad)}</small></td>
      <td>${esc(purchase.asientos.join(", "))}</td>
      <td>${esc(purchase.pago)}</td>
      <td><strong>${cop(purchase.total)}</strong></td>
      <td>${esc(purchase.estado)}</td>
    </tr>`).join("");
  status.hidden = true;
  $("#purchaseTable").hidden = false;
}

loadPurchases();