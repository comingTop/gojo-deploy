; gta-storymode.ahk - hands-off entry into STORY MODE on the GTA V landing menu.
;
; GTA V always boots to the landing menu (QUIT / SETTINGS / ... / ONLINE / STORY MODE)
; and waits for a human to pick one. This script clicks STORY MODE (bottom-right of the
; menu) repeatedly until the in-game ScriptHookV webhook on 127.0.0.1:6721 answers 200,
; which only happens once the save has loaded into free-roam -- so the clicks stop the
; moment we are actually in the world and cannot disturb gameplay afterwards.
;
; Launched by start-session.ps1 right after the GTA launch is requested. Run with the
; portable interpreter: C:\gojo\tools\AutoHotkeyU64.exe C:\gojo\autostart\gta-storymode.ahk
; Manual host tuning: the STORY MODE click is at a fixed fraction of the GTA window; if
; the menu item is missed, adjust STORY_X / STORY_Y below and re-test.
#NoEnv
#SingleInstance Force
SetTitleMatchMode, 2
CoordMode, Mouse, Screen

global STORY_X := 0.925   ; STORY MODE x as a fraction of the GTA window width
global STORY_Y := 0.96    ; STORY MODE y as a fraction of the GTA window height

; Wait up to 10 minutes for the GTA window to appear (cold boot + Rockstar launcher).
WinWait, Grand Theft Auto V,, 600
if ErrorLevel
    ExitApp

; Let the legal screens / menu finish rendering before the first click.
Sleep, 20000

Loop, 40 {
    if InGame()
        break
    WinGet, gtaId, ID, Grand Theft Auto V
    if (gtaId) {
        WinActivate, ahk_id %gtaId%
        WinGetPos, wx, wy, ww, wh, ahk_id %gtaId%
        cx := wx + ww * STORY_X
        cy := wy + wh * STORY_Y
        Click, %cx%, %cy%
    }
    Sleep, 6000
}
ExitApp

; True once the in-game mod webhook answers, i.e. we are in free-roam.
InGame() {
    try {
        whr := ComObjCreate("WinHttp.WinHttpRequest.5.1")
        whr.SetTimeouts(2000, 2000, 2000, 2000)
        whr.Open("GET", "http://127.0.0.1:6721/health", false)
        whr.Send()
        return (whr.Status = 200)
    } catch e {
        return false
    }
}
