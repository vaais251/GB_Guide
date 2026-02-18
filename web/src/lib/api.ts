/**
 * GB Guide — API Client
 *
 * Centralized HTTP client for communicating with the FastAPI backend.
 * Automatically attaches JWT token from localStorage to protected requests.
 */

const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ─── Token helpers ───────────────────────────────────────────── */

export function getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("gbg_token");
}

export function setToken(token: string): void {
    localStorage.setItem("gbg_token", token);
}

export function removeToken(): void {
    localStorage.removeItem("gbg_token");
}

/* ─── Core fetch wrapper ──────────────────────────────────────── */

interface FetchOptions extends RequestInit {
    /** If true, attaches the Bearer token. Default: false */
    auth?: boolean;
}

async function apiFetch<T = unknown>(
    path: string,
    options: FetchOptions = {},
): Promise<T> {
    const { auth = false, headers: extraHeaders, ...rest } = options;

    const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...(extraHeaders as Record<string, string>),
    };

    if (auth) {
        const token = getToken();
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }
    }

    const res = await fetch(`${API_BASE_URL}${path}`, {
        headers,
        ...rest,
    });

    // Parse JSON (or return empty object for 204)
    const data = res.status === 204 ? ({} as T) : await res.json();

    if (!res.ok) {
        const message =
            (data as { detail?: string }).detail ||
            `Request failed with status ${res.status}`;
        throw new Error(message);
    }

    return data as T;
}

/* ─── Auth endpoints ──────────────────────────────────────────── */

export interface LoginPayload {
    email: string;
    password: string;
}

export interface RegisterPayload {
    email: string;
    password: string;
    full_name: string;
    city?: string;
    phone_number?: string;
    role?: string;
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
}

export interface UserResponse {
    id: number;
    email: string;
    full_name: string;
    city: string | null;
    phone_number: string | null;
    role: string;
    created_at: string;
}

export async function login(payload: LoginPayload): Promise<TokenResponse> {
    // OAuth2PasswordRequestForm expects form-encoded data
    const body = new URLSearchParams({
        username: payload.email,
        password: payload.password,
    });

    const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Login failed");
    return data as TokenResponse;
}

export async function register(
    payload: RegisterPayload,
): Promise<UserResponse> {
    return apiFetch<UserResponse>("/api/auth/register", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export async function getMe(): Promise<UserResponse> {
    return apiFetch<UserResponse>("/api/auth/me", { auth: true });
}

/* ─── Hotel endpoints ─────────────────────────────────────────── */

export interface HotelPayload {
    name: string;
    location: string;
    city: string;
    description?: string;
    images?: string[];
}

export interface RoomPayload {
    room_type: string;
    price_per_night: number;
    capacity: number;
    is_available?: boolean;
}

export interface RoomResponse {
    id: number;
    hotel_id: number;
    room_type: string;
    price_per_night: number;
    capacity: number;
    is_available: boolean;
}

export interface HotelResponse {
    id: number;
    owner_id: number;
    name: string;
    location: string;
    city: string;
    description: string | null;
    images: string[] | null;
    created_at: string;
    rooms: RoomResponse[];
}

export async function createHotel(
    payload: HotelPayload,
): Promise<HotelResponse> {
    return apiFetch<HotelResponse>("/api/hotels", {
        method: "POST",
        body: JSON.stringify(payload),
        auth: true,
    });
}

export async function listHotels(city?: string): Promise<HotelResponse[]> {
    const query = city ? `?city=${encodeURIComponent(city)}` : "";
    return apiFetch<HotelResponse[]>(`/api/hotels${query}`);
}

export async function getHotel(hotelId: number): Promise<HotelResponse> {
    return apiFetch<HotelResponse>(`/api/hotels/${hotelId}`);
}

export async function getMyHotels(): Promise<HotelResponse[]> {
    return apiFetch<HotelResponse[]>("/api/hotels/my/hotels", { auth: true });
}

export async function addRoom(
    hotelId: number,
    payload: RoomPayload,
): Promise<RoomResponse> {
    return apiFetch<RoomResponse>(`/api/hotels/${hotelId}/rooms`, {
        method: "POST",
        body: JSON.stringify(payload),
        auth: true,
    });
}
