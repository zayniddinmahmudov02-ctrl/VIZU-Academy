"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowDown, ArrowLeft, ArrowUp, Heart, ListPlus, ListMusic, Lock, Pause, Play, Plus, Search, Trash2 } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import {
  addToPlaylist, createPlaylist, deletePlaylist, getHistory, getPlaylist, getPlaylists, getSongs, removeFromPlaylist, renamePlaylist, reorderPlaylist, setFavorite,
} from "../services/medien-service";
import { currentSong, usePlayerStore } from "../store/player-store";
import type { Playlist, SongCard } from "../types";
import { formatTime } from "./global-audio-player";
import { Cover, EmptyState, Pager, PriceTag, PurchaseButton, SectionTitle, useDebounced } from "./media-ui";
import { MedienStatsSection } from "./medien-stats";

type Tab = "discover" | "playlists" | "favorites" | "history";
const PAGE_SIZE = 30;

function SongRow({ song, list, index, playlists, inPlaylist }: { song: SongCard; list: SongCard[]; index: number; playlists: Playlist[]; inPlaylist?: { id: string; own: boolean; move: (dir: -1 | 1) => void; remove: () => void; first: boolean; last: boolean } }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [menu, setMenu] = useState(false);
  const current = usePlayerStore((s) => currentSong(s));
  const playing = usePlayerStore((s) => s.playing);
  const isCurrent = current?.id === song.id;
  const fav = useMutation({
    mutationFn: () => setFavorite(song.id, !song.favorite),
    onSuccess: (r) => {
      usePlayerStore.getState().patchSong(song.id, { favorite: r.favorite });
      void queryClient.invalidateQueries({ queryKey: ["medien-songs"] });
      void queryClient.invalidateQueries({ queryKey: ["medien-history"] });
    },
  });
  const add = useMutation({
    mutationFn: (playlistId: string) => addToPlaylist(playlistId, song.id),
    onSuccess: () => { setMenu(false); void queryClient.invalidateQueries({ queryKey: ["medien-playlists"] }); void queryClient.invalidateQueries({ queryKey: ["medien-playlist"] }); },
  });
  const own = playlists.filter((p) => !p.official);

  function play() {
    if (isCurrent) {
      usePlayerStore.getState().toggle();
      return;
    }
    // a new song: the large vinyl player opens (the music then keeps going on every other page — floating disc)
    usePlayerStore.getState().playQueue(list, index);
    usePlayerStore.getState().openLargePlayer();
  }

  return (
    <li className={cn("group relative flex items-center gap-3 rounded-xl p-2 transition hover:bg-surface-hover", isCurrent && "bg-accent-blue/10")} data-testid="song-row" data-id={song.id} data-current={isCurrent ? "1" : "0"}>
      <button type="button" onClick={play} disabled={song.locked} aria-label={`${isCurrent && playing ? t("medien.playerPause") : t("medien.playerPlay")}: ${song.title}`} data-testid="song-play"
              className="relative h-12 w-12 shrink-0 overflow-hidden rounded-lg disabled:cursor-not-allowed">
        <Cover src={song.cover_url} kind="SONG" className="h-full w-full" />
        <span className={cn("absolute inset-0 flex items-center justify-center bg-black/45 text-white transition", isCurrent ? "opacity-100" : "opacity-0 group-hover:opacity-100 group-focus-within:opacity-100")}>
          {song.locked ? <Lock size={16} /> : isCurrent && playing ? <Pause size={18} /> : <Play size={18} />}
        </span>
      </button>
      <div className="min-w-0 flex-1">
        <p className={cn("truncate text-sm font-semibold", isCurrent ? "text-accent-blue" : "text-text-primary")} data-testid="song-title">{song.title}</p>
        <p className="truncate text-xs text-text-muted">{[song.artist, song.album].filter(Boolean).join(" · ")}</p>
      </div>
      <div className="hidden shrink-0 items-center gap-2 text-xs text-text-muted sm:flex">
        {song.level && <span className="rounded-full bg-surface-hover px-2 py-0.5 font-semibold">{song.level}</span>}
        {song.genre && <span>{song.genre}</span>}
      </div>
      {song.locked ? <PurchaseButton item={song} size="sm" /> : <PriceTag item={song} className="hidden sm:inline-flex" />}
      <span className="w-10 shrink-0 text-right text-xs tabular-nums text-text-muted">{song.duration_ms ? formatTime(song.duration_ms / 1000) : ""}</span>
      <div className="flex shrink-0 items-center">
        {inPlaylist?.own && (
          <>
            <button aria-label={t("medien.moveUp")} disabled={inPlaylist.first} onClick={() => inPlaylist.move(-1)} className="rounded p-1.5 text-text-muted hover:text-accent-blue disabled:opacity-30" data-testid="song-up"><ArrowUp size={14} /></button>
            <button aria-label={t("medien.moveDown")} disabled={inPlaylist.last} onClick={() => inPlaylist.move(1)} className="rounded p-1.5 text-text-muted hover:text-accent-blue disabled:opacity-30" data-testid="song-down"><ArrowDown size={14} /></button>
            <button aria-label={t("medien.removeFromPlaylist")} onClick={inPlaylist.remove} className="rounded p-1.5 text-text-muted hover:text-danger" data-testid="song-remove"><Trash2 size={14} /></button>
          </>
        )}
        <button type="button" aria-label={t("medien.playerFavorite")} aria-pressed={song.favorite} onClick={() => fav.mutate()} data-testid="song-favorite"
                className={cn("rounded-full p-2 transition", song.favorite ? "text-danger" : "text-text-muted hover:text-danger")}>
          <Heart size={16} className={song.favorite ? "fill-current" : ""} />
        </button>
        {!song.locked && (
          <div className="relative">
            <button type="button" aria-label={t("medien.addToPlaylist")} aria-expanded={menu} onClick={() => setMenu((v) => !v)} data-testid="song-add-playlist" className="rounded-full p-2 text-text-muted hover:text-accent-blue"><ListPlus size={16} /></button>
            {menu && (
              <div className="absolute right-0 top-full z-20 w-56 rounded-xl bg-surface-card p-2 shadow-[var(--shadow-lg)] ring-1 ring-surface-border" data-testid="playlist-menu">
                {own.length === 0 && <p className="p-2 text-xs text-text-muted">{t("medien.noOwnPlaylists")}</p>}
                {own.map((p) => <button key={p.id} className="block w-full truncate rounded-lg px-2 py-1.5 text-left text-sm hover:bg-surface-hover" onClick={() => add.mutate(p.id)} data-testid="playlist-menu-item">{p.name}</button>)}
              </div>
            )}
          </div>
        )}
      </div>
    </li>
  );
}

function SongList({ songs, playlists, empty, inPlaylist }: { songs: SongCard[]; playlists: Playlist[]; empty: string; inPlaylist?: (s: SongCard, i: number) => Parameters<typeof SongRow>[0]["inPlaylist"] }) {
  if (!songs.length) return <EmptyState text={empty} />;
  return <ul className="space-y-1" data-testid="song-list">{songs.map((s, i) => <SongRow key={s.id} song={s} list={songs} index={i} playlists={playlists} inPlaylist={inPlaylist?.(s, i)} />)}</ul>;
}

function PlaylistsTab({ playlists }: { playlists: Playlist[] }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [rename, setRename] = useState<string | null>(null);
  const detail = useQuery({ queryKey: ["medien-playlist", selected], queryFn: () => getPlaylist(selected!), enabled: !!selected });
  const refresh = () => { void queryClient.invalidateQueries({ queryKey: ["medien-playlists"] }); void queryClient.invalidateQueries({ queryKey: ["medien-playlist"] }); };
  const create = useMutation({ mutationFn: () => createPlaylist(name.trim()), onSuccess: (p) => { setName(""); setSelected(p.id); refresh(); } });
  const del = useMutation({ mutationFn: (id: string) => deletePlaylist(id), onSuccess: () => { setSelected(null); refresh(); } });
  const ren = useMutation({ mutationFn: ({ id, n }: { id: string; n: string }) => renamePlaylist(id, n), onSuccess: () => { setRename(null); refresh(); } });
  const order = useMutation({ mutationFn: ({ id, ids }: { id: string; ids: string[] }) => reorderPlaylist(id, ids), onSuccess: refresh });
  const drop = useMutation({ mutationFn: ({ id, song }: { id: string; song: string }) => removeFromPlaylist(id, song), onSuccess: refresh });

  const pl = detail.data;
  const move = (i: number, dir: -1 | 1) => {
    if (!pl) return;
    const ids = pl.songs.map((s) => s.id);
    [ids[i], ids[i + dir]] = [ids[i + dir], ids[i]];
    order.mutate({ id: pl.id, ids });
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[300px_1fr]" data-testid="playlists-tab">
      <div className="space-y-3">
        <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); if (name.trim()) create.mutate(); }}>
          <input value={name} onChange={(e) => setName(e.target.value)} maxLength={160} placeholder={t("medien.playlistName")} aria-label={t("medien.playlistName")} data-testid="playlist-create-input"
                 className="min-w-0 flex-1 rounded-xl bg-surface-card px-3 py-2 text-sm ring-1 ring-surface-border" />
          <button type="submit" disabled={!name.trim() || create.isPending} className="flex items-center gap-1 rounded-xl bg-accent-blue px-3 text-sm font-semibold text-white disabled:opacity-50" data-testid="playlist-create"><Plus size={15} /> {t("medien.create")}</button>
        </form>
        {!playlists.length && <EmptyState text={t("medien.noPlaylists")} />}
        <ul className="space-y-1.5">
          {playlists.map((p) => (
            <li key={p.id}>
              <button onClick={() => setSelected(p.id)} data-testid="playlist-card" data-id={p.id} data-official={p.official ? "1" : "0"}
                      className={cn("flex w-full items-center gap-3 rounded-xl p-2 text-left ring-1 transition", selected === p.id ? "bg-accent-blue/10 ring-accent-blue/40" : "bg-surface-card ring-surface-border hover:bg-surface-hover")}>
                <Cover src={p.cover_url} kind="SONG" className="h-12 w-12 shrink-0 rounded-lg" />
                <span className="min-w-0"><span className="block truncate text-sm font-semibold text-text-primary">{p.name}</span>
                  <span className="block text-xs text-text-muted">{p.official ? "VIZU · " : ""}{t("medien.songsCount", { n: p.song_count })}</span></span>
              </button>
            </li>
          ))}
        </ul>
      </div>
      <div>
        {!selected && <EmptyState text={t("medien.selectPlaylist")} />}
        {selected && pl && (
          <div className="space-y-4" data-testid="playlist-detail">
            <div className="flex flex-wrap items-center gap-3">
              {rename !== null ? (
                <form className="flex flex-1 gap-2" onSubmit={(e) => { e.preventDefault(); if (rename.trim()) ren.mutate({ id: pl.id, n: rename.trim() }); }}>
                  <input value={rename} onChange={(e) => setRename(e.target.value)} autoFocus maxLength={160} aria-label={t("medien.playlistName")} data-testid="playlist-rename-input" className="min-w-0 flex-1 rounded-xl bg-surface-card px-3 py-2 text-sm ring-1 ring-surface-border" />
                  <button className="rounded-xl bg-accent-blue px-3 text-sm font-semibold text-white" data-testid="playlist-rename-save">{t("medien.save")}</button>
                </form>
              ) : <h3 className="flex-1 truncate text-xl font-bold text-text-primary" data-testid="playlist-title">{pl.name}</h3>}
              <button disabled={!pl.songs.length} onClick={() => { usePlayerStore.getState().playQueue(pl.songs); usePlayerStore.getState().openLargePlayer(); }} className="flex items-center gap-2 rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white disabled:opacity-50" data-testid="playlist-play"><Play size={15} /> {t("medien.playAll")}</button>
              {!pl.official && rename === null && (
                <>
                  <button onClick={() => setRename(pl.name)} className="rounded-xl px-3 py-2 text-sm font-semibold ring-1 ring-surface-border hover:bg-surface-hover" data-testid="playlist-rename">{t("medien.rename")}</button>
                  <button onClick={() => del.mutate(pl.id)} className="rounded-xl px-3 py-2 text-sm font-semibold text-danger ring-1 ring-danger/30 hover:bg-danger/10" data-testid="playlist-delete">{t("medien.delete")}</button>
                </>
              )}
            </div>
            <SongList songs={pl.songs} playlists={playlists} empty={t("medien.emptyPlaylist")}
                      inPlaylist={(s, i) => ({ id: pl.id, own: !pl.official, move: (d) => move(i, d), remove: () => drop.mutate({ id: pl.id, song: s.id }), first: i === 0, last: i === pl.songs.length - 1 })} />
          </div>
        )}
      </div>
    </div>
  );
}

/** Musik: discover (featured, new, all), search, playlists (own + official), favorites and play history. Starting a song
 * hands the visible list to the global player and opens the large vinyl player; the music keeps playing on every other page
 * (floating disc there) and coming back here shows this page again without restarting it. */
export default function MusikClient() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<Tab>("discover");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const q = useDebounced(search);
  const playlists = useQuery({ queryKey: ["medien-playlists"], queryFn: getPlaylists });
  const featured = useQuery({ queryKey: ["medien-songs", "featured"], queryFn: () => getSongs({ featured: true, page_size: 8 }), enabled: tab === "discover" && !q });
  const fresh = useQuery({ queryKey: ["medien-songs", "new"], queryFn: () => getSongs({ sort: "new", page_size: 8 }), enabled: tab === "discover" && !q });
  const all = useQuery({ queryKey: ["medien-songs", "all", q, page], queryFn: () => getSongs({ q, page, page_size: PAGE_SIZE, sort: q ? "popular" : "title" }), enabled: tab === "discover", placeholderData: (p) => p });
  const favorites = useQuery({ queryKey: ["medien-songs", "favorites"], queryFn: () => getSongs({ favorites: true, page_size: 60 }), enabled: tab === "favorites" });
  const history = useQuery({ queryKey: ["medien-history"], queryFn: getHistory, enabled: tab === "history" });
  const pls = playlists.data ?? [];
  const tabs: [Tab, string][] = [["discover", t("medien.discover")], ["playlists", t("medien.playlists")], ["favorites", t("medien.favorites")], ["history", t("medien.history")]];

  return (
    <div className="space-y-6" data-testid="musik">
      <Link href="/medien" className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary hover:text-accent-blue"><ArrowLeft size={16} /> {t("medien.title")}</Link>
      <header className="rounded-3xl bg-gradient-to-br from-fuchsia-700 via-violet-900 to-indigo-950 p-6 text-white shadow-[var(--shadow-md)] sm:p-9">
        <h1 className="flex items-center gap-3 text-2xl font-extrabold sm:text-4xl"><ListMusic /> {t("medien.music")}</h1>
        <p className="mt-1 text-white/75">{t("medien.musicDesc")}</p>
      </header>

      <MedienStatsSection kind="MUSIC" />

      <div className="flex flex-wrap items-center gap-2" role="tablist">
        {tabs.map(([id, label]) => (
          <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id)} data-testid={`musik-tab-${id}`}
                  className={cn("rounded-full px-4 py-1.5 text-sm font-semibold transition", tab === id ? "bg-accent-blue text-white" : "bg-surface-card text-text-secondary ring-1 ring-surface-border hover:bg-surface-hover")}>{label}</button>
        ))}
        {tab === "discover" && (
          <label className="relative ml-auto min-w-[14rem] flex-1 sm:max-w-xs">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} placeholder={t("medien.searchSongs")} aria-label={t("medien.searchSongs")} data-testid="song-search"
                   className="w-full rounded-xl bg-surface-card py-2 pl-9 pr-3 text-sm ring-1 ring-surface-border" />
          </label>
        )}
      </div>

      {tab === "discover" && (
        <div className="space-y-8">
          {!q && !!featured.data?.items.length && <section data-testid="songs-featured"><SectionTitle>{t("medien.featuredSongs")}</SectionTitle><SongList songs={featured.data.items} playlists={pls} empty="" /></section>}
          {!q && !!fresh.data?.items.length && <section data-testid="songs-new"><SectionTitle>{t("medien.newSongs")}</SectionTitle><SongList songs={fresh.data.items} playlists={pls} empty="" /></section>}
          <section data-testid="songs-all">
            <SectionTitle>{q ? t("medien.searchResults") : t("medien.allSongs")}</SectionTitle>
            {all.isLoading ? <p className="text-sm text-text-secondary">{t("medien.loading")}</p> : <SongList songs={all.data?.items ?? []} playlists={pls} empty={t("medien.noSongs")} />}
            <Pager page={page} pageSize={PAGE_SIZE} total={all.data?.total ?? 0} onChange={setPage} />
          </section>
        </div>
      )}
      {tab === "playlists" && <PlaylistsTab playlists={pls} />}
      {tab === "favorites" && <section data-testid="songs-favorites"><SongList songs={favorites.data?.items ?? []} playlists={pls} empty={t("medien.noFavorites")} /></section>}
      {tab === "history" && <section data-testid="songs-history"><SongList songs={history.data ?? []} playlists={pls} empty={t("medien.noHistory")} /></section>}
    </div>
  );
}
