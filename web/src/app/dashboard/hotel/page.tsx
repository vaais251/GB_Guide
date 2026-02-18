"use client";

import { useEffect, useState, useCallback } from "react";
import {
    login,
    setToken,
    getToken,
    removeToken,
    getMe,
    getMyHotels,
    createHotel,
    addRoom,
    type UserResponse,
    type HotelResponse as HotelData,
    type LoginPayload,
    type HotelPayload,
    type RoomPayload,
    register,
    type RegisterPayload,
} from "@/lib/api";

/* ─── Types ───────────────────────────────────────────────────── */

type View = "login" | "dashboard";

/* ─── Main Page Component ─────────────────────────────────────── */

export default function HotelDashboard() {
    const [view, setView] = useState<View>("login");
    const [user, setUser] = useState<UserResponse | null>(null);
    const [hotels, setHotels] = useState<HotelData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // ── Check existing token on mount ────────────────────────────
    useEffect(() => {
        const token = getToken();
        if (token) {
            getMe()
                .then((u) => {
                    setUser(u);
                    setView("dashboard");
                })
                .catch(() => {
                    removeToken();
                })
                .finally(() => setLoading(false));
        } else {
            setLoading(false);
        }
    }, []);

    const refreshHotels = useCallback(async () => {
        try {
            const data = await getMyHotels();
            setHotels(data);
        } catch (err) {
            console.error("Failed to fetch hotels:", err);
        }
    }, []);

    // ── Load hotels when entering dashboard ──────────────────────
    useEffect(() => {
        if (view === "dashboard" && user) {
            refreshHotels();
        }
    }, [view, user, refreshHotels]);

    const handleLogin = async (payload: LoginPayload) => {
        setError(null);
        try {
            const { access_token } = await login(payload);
            setToken(access_token);
            const u = await getMe();
            setUser(u);
            setView("dashboard");
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Login failed");
        }
    };

    const handleRegister = async (payload: RegisterPayload) => {
        setError(null);
        try {
            await register(payload);
            // Auto-login after registration
            const { access_token } = await login({
                email: payload.email,
                password: payload.password,
            });
            setToken(access_token);
            const u = await getMe();
            setUser(u);
            setView("dashboard");
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Registration failed");
        }
    };

    const handleLogout = () => {
        removeToken();
        setUser(null);
        setHotels([]);
        setView("login");
    };

    if (loading) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-600 border-t-emerald-400" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 font-sans text-white">
            {view === "login" ? (
                <LoginRegisterView
                    onLogin={handleLogin}
                    onRegister={handleRegister}
                    error={error}
                />
            ) : (
                <DashboardView
                    user={user!}
                    hotels={hotels}
                    onLogout={handleLogout}
                    onRefresh={refreshHotels}
                    setError={setError}
                    error={error}
                />
            )}
        </div>
    );
}

/* ═══════════════════════════════════════════════════════════════════
   LOGIN / REGISTER VIEW
   ═══════════════════════════════════════════════════════════════════ */

function LoginRegisterView({
    onLogin,
    onRegister,
    error,
}: {
    onLogin: (p: LoginPayload) => Promise<void>;
    onRegister: (p: RegisterPayload) => Promise<void>;
    error: string | null;
}) {
    const [isRegistering, setIsRegistering] = useState(false);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [fullName, setFullName] = useState("");
    const [city, setCity] = useState("");
    const [submitting, setSubmitting] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitting(true);
        try {
            if (isRegistering) {
                await onRegister({
                    email,
                    password,
                    full_name: fullName,
                    city: city || undefined,
                    role: "hotel_owner",
                });
            } else {
                await onLogin({ email, password });
            }
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center px-4">
            <div className="w-full max-w-md">
                {/* Logo */}
                <div className="mb-8 text-center">
                    <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-400 to-cyan-500 text-2xl font-black text-white shadow-lg shadow-emerald-500/25">
                        GB
                    </div>
                    <h1 className="mt-4 text-3xl font-bold tracking-tight text-white">
                        Hotel Owner Portal
                    </h1>
                    <p className="mt-2 text-slate-400">
                        {isRegistering
                            ? "Create your hotel owner account"
                            : "Sign in to manage your properties"}
                    </p>
                </div>

                {/* Card */}
                <div className="rounded-2xl border border-slate-700/50 bg-slate-800/60 p-8 shadow-2xl backdrop-blur-sm">
                    <form onSubmit={handleSubmit} className="space-y-5">
                        {isRegistering && (
                            <>
                                <InputField
                                    id="full_name"
                                    label="Full Name"
                                    value={fullName}
                                    onChange={setFullName}
                                    placeholder="Ali Khan"
                                    required
                                />
                                <InputField
                                    id="city"
                                    label="City (optional)"
                                    value={city}
                                    onChange={setCity}
                                    placeholder="Gilgit"
                                />
                            </>
                        )}
                        <InputField
                            id="email"
                            label="Email"
                            type="email"
                            value={email}
                            onChange={setEmail}
                            placeholder="owner@hotel.com"
                            required
                        />
                        <InputField
                            id="password"
                            label="Password"
                            type="password"
                            value={password}
                            onChange={setPassword}
                            placeholder="••••••••"
                            required
                            minLength={8}
                        />

                        {error && (
                            <div className="rounded-lg bg-red-500/10 p-3 text-sm text-red-400 border border-red-500/20">
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={submitting}
                            className="w-full rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-500/25 transition-all hover:shadow-emerald-500/40 hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {submitting
                                ? "Please wait…"
                                : isRegistering
                                    ? "Create Account & Login"
                                    : "Sign In"}
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <button
                            onClick={() => setIsRegistering(!isRegistering)}
                            className="text-sm text-slate-400 underline-offset-4 hover:text-emerald-400 hover:underline transition-colors"
                        >
                            {isRegistering
                                ? "Already have an account? Sign in"
                                : "Need an account? Register as Hotel Owner"}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════════════════════════════
   DASHBOARD VIEW
   ═══════════════════════════════════════════════════════════════════ */

function DashboardView({
    user,
    hotels,
    onLogout,
    onRefresh,
    setError,
    error,
}: {
    user: UserResponse;
    hotels: HotelData[];
    onLogout: () => void;
    onRefresh: () => Promise<void>;
    setError: (e: string | null) => void;
    error: string | null;
}) {
    const [showHotelForm, setShowHotelForm] = useState(false);
    const [addingRoomForHotel, setAddingRoomForHotel] = useState<number | null>(
        null,
    );

    return (
        <div className="mx-auto max-w-6xl px-4 py-8">
            {/* ── Header ──────────────────────────────────────────────── */}
            <header className="mb-10 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-500 text-lg font-black text-white shadow-lg shadow-emerald-500/25">
                        GB
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight">
                            Hotel Dashboard
                        </h1>
                        <p className="text-sm text-slate-400">
                            Welcome, {user.full_name} ·{" "}
                            <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-400 ring-1 ring-inset ring-emerald-500/20">
                                {user.role}
                            </span>
                        </p>
                    </div>
                </div>
                <button
                    onClick={onLogout}
                    className="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm text-slate-300 transition-colors hover:bg-slate-700 hover:text-white"
                >
                    Sign Out
                </button>
            </header>

            {/* ── Error Banner ────────────────────────────────────────── */}
            {error && (
                <div className="mb-6 rounded-lg bg-red-500/10 p-4 text-sm text-red-400 border border-red-500/20">
                    {error}
                    <button
                        onClick={() => setError(null)}
                        className="ml-3 text-red-300 hover:text-red-200 underline text-xs"
                    >
                        dismiss
                    </button>
                </div>
            )}

            {/* ── Stats Row ───────────────────────────────────────────── */}
            <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
                <StatCard
                    label="Total Hotels"
                    value={hotels.length}
                    icon="🏨"
                />
                <StatCard
                    label="Total Rooms"
                    value={hotels.reduce((sum, h) => sum + (h.rooms?.length || 0), 0)}
                    icon="🛏️"
                />
                <StatCard
                    label="Cities"
                    value={new Set(hotels.map((h) => h.city)).size}
                    icon="📍"
                />
            </div>

            {/* ── Add Hotel Button ────────────────────────────────────── */}
            <div className="mb-6 flex items-center justify-between">
                <h2 className="text-xl font-semibold">Your Properties</h2>
                <button
                    onClick={() => {
                        setShowHotelForm(!showHotelForm);
                        setError(null);
                    }}
                    className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 px-5 py-2.5 text-sm font-semibold shadow-lg shadow-emerald-500/25 transition-all hover:shadow-emerald-500/40 hover:brightness-110"
                >
                    <span className="text-lg">+</span>
                    {showHotelForm ? "Cancel" : "Add Hotel"}
                </button>
            </div>

            {/* ── New Hotel Form ──────────────────────────────────────── */}
            {showHotelForm && (
                <CreateHotelForm
                    onCreated={() => {
                        setShowHotelForm(false);
                        onRefresh();
                    }}
                    setError={setError}
                />
            )}

            {/* ── Hotels Grid ─────────────────────────────────────────── */}
            {hotels.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-800/30 p-16 text-center">
                    <div className="mx-auto mb-4 text-5xl">🏔️</div>
                    <p className="text-lg text-slate-400">No hotels yet</p>
                    <p className="mt-1 text-sm text-slate-500">
                        Click &quot;Add Hotel&quot; to list your first property
                    </p>
                </div>
            ) : (
                <div className="space-y-6">
                    {hotels.map((hotel) => (
                        <HotelCard
                            key={hotel.id}
                            hotel={hotel}
                            isAddingRoom={addingRoomForHotel === hotel.id}
                            onToggleAddRoom={() =>
                                setAddingRoomForHotel(
                                    addingRoomForHotel === hotel.id ? null : hotel.id,
                                )
                            }
                            onRoomAdded={onRefresh}
                            setError={setError}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}

/* ═══════════════════════════════════════════════════════════════════
   HOTEL CARD
   ═══════════════════════════════════════════════════════════════════ */

function HotelCard({
    hotel,
    isAddingRoom,
    onToggleAddRoom,
    onRoomAdded,
    setError,
}: {
    hotel: HotelData;
    isAddingRoom: boolean;
    onToggleAddRoom: () => void;
    onRoomAdded: () => Promise<void>;
    setError: (e: string | null) => void;
}) {
    return (
        <div className="overflow-hidden rounded-2xl border border-slate-700/50 bg-slate-800/50 shadow-xl backdrop-blur-sm transition-all hover:border-slate-600/50">
            {/* Hotel header */}
            <div className="flex items-start justify-between p-6">
                <div>
                    <h3 className="text-xl font-bold text-white">{hotel.name}</h3>
                    <div className="mt-1 flex items-center gap-3 text-sm text-slate-400">
                        <span className="flex items-center gap-1">
                            📍 {hotel.city}
                        </span>
                        <span className="text-slate-600">·</span>
                        <span>{hotel.location}</span>
                    </div>
                    {hotel.description && (
                        <p className="mt-3 max-w-xl text-sm leading-relaxed text-slate-300">
                            {hotel.description}
                        </p>
                    )}
                </div>
                <button
                    onClick={onToggleAddRoom}
                    className={`rounded-lg px-4 py-2 text-sm font-medium transition-all ${isAddingRoom
                            ? "bg-slate-700 text-slate-300 hover:bg-slate-600"
                            : "bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/20 hover:bg-emerald-500/20"
                        }`}
                >
                    {isAddingRoom ? "Cancel" : "+ Add Room"}
                </button>
            </div>

            {/* Add room form */}
            {isAddingRoom && (
                <div className="border-t border-slate-700/50 bg-slate-900/30 p-6">
                    <AddRoomForm
                        hotelId={hotel.id}
                        onCreated={() => {
                            onToggleAddRoom();
                            onRoomAdded();
                        }}
                        setError={setError}
                    />
                </div>
            )}

            {/* Rooms table */}
            {hotel.rooms && hotel.rooms.length > 0 && (
                <div className="border-t border-slate-700/30">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-slate-700/30 text-left text-xs uppercase tracking-wider text-slate-500">
                                <th className="px-6 py-3">Room Type</th>
                                <th className="px-6 py-3">Price / Night</th>
                                <th className="px-6 py-3">Capacity</th>
                                <th className="px-6 py-3">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700/20">
                            {hotel.rooms.map((room) => (
                                <tr
                                    key={room.id}
                                    className="text-slate-300 transition-colors hover:bg-slate-700/20"
                                >
                                    <td className="px-6 py-3 font-medium text-white">
                                        {room.room_type}
                                    </td>
                                    <td className="px-6 py-3">
                                        PKR {room.price_per_night.toLocaleString()}
                                    </td>
                                    <td className="px-6 py-3">{room.capacity} guests</td>
                                    <td className="px-6 py-3">
                                        <span
                                            className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${room.is_available
                                                    ? "bg-emerald-500/10 text-emerald-400 ring-1 ring-inset ring-emerald-500/20"
                                                    : "bg-red-500/10 text-red-400 ring-1 ring-inset ring-red-500/20"
                                                }`}
                                        >
                                            {room.is_available ? "Available" : "Booked"}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* No rooms message */}
            {(!hotel.rooms || hotel.rooms.length === 0) && !isAddingRoom && (
                <div className="border-t border-slate-700/30 px-6 py-4 text-center text-sm text-slate-500">
                    No rooms yet — click &quot;+ Add Room&quot; to get started
                </div>
            )}
        </div>
    );
}

/* ═══════════════════════════════════════════════════════════════════
   CREATE HOTEL FORM
   ═══════════════════════════════════════════════════════════════════ */

function CreateHotelForm({
    onCreated,
    setError,
}: {
    onCreated: () => void;
    setError: (e: string | null) => void;
}) {
    const [name, setName] = useState("");
    const [location, setLocation] = useState("");
    const [city, setCity] = useState("");
    const [description, setDescription] = useState("");
    const [submitting, setSubmitting] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitting(true);
        setError(null);
        try {
            const payload: HotelPayload = {
                name,
                location,
                city,
                description: description || undefined,
            };
            await createHotel(payload);
            onCreated();
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Failed to create hotel");
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="mb-6 rounded-2xl border border-emerald-500/20 bg-slate-800/50 p-6 shadow-xl backdrop-blur-sm">
            <h3 className="mb-4 text-lg font-semibold text-white flex items-center gap-2">
                <span className="text-xl">🏨</span> New Hotel Property
            </h3>
            <form onSubmit={handleSubmit} className="grid gap-4 sm:grid-cols-2">
                <InputField
                    id="hotel_name"
                    label="Hotel Name"
                    value={name}
                    onChange={setName}
                    placeholder="Serena Hotel Gilgit"
                    required
                />
                <InputField
                    id="hotel_city"
                    label="City"
                    value={city}
                    onChange={setCity}
                    placeholder="Gilgit"
                    required
                />
                <div className="sm:col-span-2">
                    <InputField
                        id="hotel_location"
                        label="Full Address"
                        value={location}
                        onChange={setLocation}
                        placeholder="Jutial, Gilgit 15100"
                        required
                    />
                </div>
                <div className="sm:col-span-2">
                    <label
                        htmlFor="hotel_description"
                        className="mb-1.5 block text-sm font-medium text-slate-300"
                    >
                        Description (optional)
                    </label>
                    <textarea
                        id="hotel_description"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="A premium hotel with mountain views and modern amenities…"
                        rows={3}
                        className="w-full rounded-lg border border-slate-600 bg-slate-900/60 px-4 py-2.5 text-sm text-white placeholder-slate-500 outline-none transition-all focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/50"
                    />
                </div>
                <div className="sm:col-span-2 flex justify-end">
                    <button
                        type="submit"
                        disabled={submitting}
                        className="rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 px-6 py-2.5 text-sm font-semibold shadow-lg shadow-emerald-500/25 transition-all hover:shadow-emerald-500/40 hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {submitting ? "Creating…" : "Create Hotel"}
                    </button>
                </div>
            </form>
        </div>
    );
}

/* ═══════════════════════════════════════════════════════════════════
   ADD ROOM FORM
   ═══════════════════════════════════════════════════════════════════ */

function AddRoomForm({
    hotelId,
    onCreated,
    setError,
}: {
    hotelId: number;
    onCreated: () => void;
    setError: (e: string | null) => void;
}) {
    const [roomType, setRoomType] = useState("");
    const [price, setPrice] = useState("");
    const [capacity, setCapacity] = useState("2");
    const [submitting, setSubmitting] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitting(true);
        setError(null);
        try {
            const payload: RoomPayload = {
                room_type: roomType,
                price_per_night: parseFloat(price),
                capacity: parseInt(capacity, 10),
            };
            await addRoom(hotelId, payload);
            onCreated();
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Failed to add room");
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-4">
            <div className="min-w-[140px] flex-1">
                <InputField
                    id={`room_type_${hotelId}`}
                    label="Room Type"
                    value={roomType}
                    onChange={setRoomType}
                    placeholder="Deluxe"
                    required
                />
            </div>
            <div className="min-w-[120px] flex-1">
                <InputField
                    id={`room_price_${hotelId}`}
                    label="Price / Night (PKR)"
                    type="number"
                    value={price}
                    onChange={setPrice}
                    placeholder="5000"
                    required
                    min="1"
                />
            </div>
            <div className="w-[100px]">
                <InputField
                    id={`room_capacity_${hotelId}`}
                    label="Capacity"
                    type="number"
                    value={capacity}
                    onChange={setCapacity}
                    placeholder="2"
                    required
                    min="1"
                    max="20"
                />
            </div>
            <button
                type="submit"
                disabled={submitting}
                className="rounded-lg bg-emerald-500/10 px-5 py-2.5 text-sm font-medium text-emerald-400 ring-1 ring-emerald-500/20 transition-all hover:bg-emerald-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
                {submitting ? "Adding…" : "Add Room"}
            </button>
        </form>
    );
}

/* ═══════════════════════════════════════════════════════════════════
   SHARED UI COMPONENTS
   ═══════════════════════════════════════════════════════════════════ */

function InputField({
    id,
    label,
    type = "text",
    value,
    onChange,
    placeholder,
    required,
    minLength,
    min,
    max,
}: {
    id: string;
    label: string;
    type?: string;
    value: string;
    onChange: (v: string) => void;
    placeholder?: string;
    required?: boolean;
    minLength?: number;
    min?: string;
    max?: string;
}) {
    return (
        <div>
            <label
                htmlFor={id}
                className="mb-1.5 block text-sm font-medium text-slate-300"
            >
                {label}
            </label>
            <input
                id={id}
                type={type}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder={placeholder}
                required={required}
                minLength={minLength}
                min={min}
                max={max}
                className="w-full rounded-lg border border-slate-600 bg-slate-900/60 px-4 py-2.5 text-sm text-white placeholder-slate-500 outline-none transition-all focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/50"
            />
        </div>
    );
}

function StatCard({
    label,
    value,
    icon,
}: {
    label: string;
    value: number;
    icon: string;
}) {
    return (
        <div className="rounded-2xl border border-slate-700/50 bg-slate-800/50 p-5 backdrop-blur-sm">
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-sm text-slate-400">{label}</p>
                    <p className="mt-1 text-3xl font-bold text-white">{value}</p>
                </div>
                <div className="text-3xl">{icon}</div>
            </div>
        </div>
    );
}
