import catIcon from "../assets/cat.png";
import { cn } from "../lib/utils";
import { useOIDCAuth } from "../hooks/useOIDCAuth";

type LoginScreenProps = {
  setAuthenticated: (isAuth: boolean) => void;
};

export const LoginScreen = ({ setAuthenticated }: LoginScreenProps) => {
  const { isChecking, isLoggingIn, error, handleLogin } = useOIDCAuth({
    setAuthenticated,
  });

  if (isChecking || isLoggingIn) {
    return (
      <div className="h-screen flex flex-col items-center justify-center bg-cream gap-4">
        <div
          className="fixed inset-0 pointer-events-none opacity-[0.035]"
          style={{
            backgroundImage: `radial-gradient(circle, var(--color-charcoal) 1px, transparent 0)`,
            backgroundSize: "22px 22px",
          }}
        />
        <div className="relative">
          <div className="absolute -inset-4 bg-amber-soft/30 rounded-full blur-2xl" />
          <img
            src={catIcon}
            alt="Simba"
            className="relative w-14 h-14 animate-bounce drop-shadow"
          />
        </div>
        <p className="text-warm-gray text-sm tracking-wide font-medium">
          {isLoggingIn ? "letting you in..." : "checking credentials..."}
        </p>
      </div>
    );
  }

  return (
    <div className="h-screen bg-cream flex items-center justify-center p-4 relative overflow-hidden">
      <div
        className="fixed inset-0 pointer-events-none opacity-[0.04]"
        style={{
          backgroundImage: `radial-gradient(circle, var(--color-charcoal) 1px, transparent 0)`,
          backgroundSize: "22px 22px",
        }}
      />

      <div className="absolute top-1/4 -left-20 w-72 h-72 rounded-full bg-leaf-pale/60 blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 -right-20 w-64 h-64 rounded-full bg-amber-pale/70 blur-3xl pointer-events-none" />

      <div className="relative w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="relative mb-5">
            <div className="absolute -inset-5 bg-amber-soft/30 rounded-full blur-2xl" />
            <img
              src={catIcon}
              alt="Simba"
              className="relative w-20 h-20 drop-shadow-lg"
            />
          </div>
          <h1
            className="text-4xl font-bold text-charcoal tracking-tight"
            style={{ fontFamily: "var(--font-display)" }}
          >
            asksimba
          </h1>
          <p className="text-warm-gray text-sm mt-1.5 tracking-wide">
            your feline knowledge companion
          </p>
        </div>

        <div
          className={cn(
            "bg-warm-white rounded-3xl border border-sand-light",
            "shadow-xl shadow-sand/30 p-8",
          )}
        >
          {error && (
            <div className="mb-5 text-sm bg-red-50 text-red-600 px-4 py-3 rounded-2xl border border-red-200">
              {error}
            </div>
          )}

          <p className="text-center text-warm-gray text-sm mb-6">
            Sign in to start chatting with Simba
          </p>

          <button
            onClick={handleLogin}
            disabled={isLoggingIn}
            className={cn(
              "w-full py-3.5 px-4 rounded-2xl text-sm font-semibold tracking-wide",
              "bg-forest text-cream",
              "shadow-md shadow-forest/20",
              "hover:bg-forest-mid hover:shadow-lg hover:shadow-forest/30",
              "active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed",
              "transition-all duration-200 cursor-pointer",
            )}
          >
            {isLoggingIn ? "Redirecting..." : "Sign in with Authelia"}
          </button>
        </div>

        <p className="text-center text-sand mt-5 text-xs tracking-widest select-none">
          * meow *
        </p>
      </div>
    </div>
  );
};
